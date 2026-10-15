import base64
import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Iterable, List, Optional

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.contrib.messages import get_messages
from django.contrib.postgres.search import TrigramSimilarity
from django.core.cache import cache
from django.core.signing import TimestampSigner
from django.db import transaction
from django.db.models import Case, F, Func, Q, Sum, Value, When
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.http import require_POST, require_safe

from registration import admin, mqtt, payments
from registration.models import (
    AttendeeOptions,
    Badge,
    Cashdrawer,
    Department,
    Discount,
    Event,
    Firebase,
    Order,
    OrderItem,
    PrintHistory,
    ShirtSizes,
    Staff,
    generate_discount_code,
    get_random_token,
)
from registration.views.attendee import get_attendee_age
from registration.views.auth import (
    RequiredTerminalRequest,
    TerminalRequest,
    device_token_required,
    no_terminal_response,
    resolve_terminal_from_request,
    staff_or_terminal_required,
)
from registration.views.ordering import (
    complete_comp_order,
    get_discount_total,
    get_order_item_option_total,
)


def flatten(l):
    return [item for sublist in l for item in sublist]


logger = logging.getLogger(__name__)

TWOPLACES = Decimal(10) ** -2


@require_safe
@staff_member_required
def onsite_admin(request):
    return render(request, "registration/spa-host.html")


@require_safe
@staff_member_required
def onsite_admin_ping(request):
    request.session.modified = True
    return JsonResponse({"success": True})


@require_safe
@staff_or_terminal_required()
def onsite_admin_terminals(request):
    terminals = list(Firebase.objects.order_by("name").all())

    data = []
    for terminal in terminals:
        data.append(
            {
                "id": terminal.id,
                "name": terminal.name,
                "cashdrawer": terminal.cashdrawer,
                "printViaMqtt": (
                    terminal.print_via_mqtt.name if terminal.print_via_mqtt else None
                ),
                "paymentType": terminal.payment_type,
                "backgroundColor": terminal.background_color,
                "foregroundColor": terminal.foreground_color,
                "squareTerminal": terminal.square_terminal_id is not None,
            }
        )

    return JsonResponse({"terminals": data})


@require_safe
@staff_member_required
def onsite_admin_context(request):
    terminals = list(Firebase.objects.order_by("name").all())

    selected_terminal = None
    mqtt_context = None

    terminal_id = request.GET.get("terminal", None)
    if terminal_id:
        terminal = Firebase.objects.get(id=terminal_id)

        selected_terminal = {
            "id": terminal.id,
            "features": {
                "card": terminal.payment_type is not None,
                "cashdrawer": terminal.cashdrawer,
                "prompt": terminal.payment_type == Firebase.MQTT_REGISTER_APP,
                "squareTerminal": terminal.square_terminal_id is not None,
            },
        }

        mqtt_context = {
            "broker": getattr(settings, "MQTT_EXTERNAL_BROKER", None),
            "auth": mqtt.get_onsite_admin_token(terminal),
        }

    events = [
        {"id": e.id, "name": e.name}
        for e in Event.objects.filter(eventEnd__gt=timezone.now())
        .order_by("eventStart")
        .all()
    ]

    context = {
        "user": {
            "id": request.user.id,
            "email": request.user.email,
        },
        "mqtt": mqtt_context,
        "shirtSizes": [{"id": s.id, "name": s.name} for s in ShirtSizes.objects.all()],
        "departments": [
            {"id": d.id, "name": d.name}
            for d in Department.objects.order_by("name").all()
        ],
        "events": events,
        "permissions": {
            "cash": request.user.has_perm("order.cash"),
            "cashAdmin": request.user.has_perm("order.cash_admin"),
            "discount": request.user.has_perm("order.discount"),
        },
        "terminals": {
            "selected": selected_terminal,
            "available": [
                {"id": terminal.id, "name": terminal.name} for terminal in terminals
            ],
        },
        "messages": get_messages_list(request),
    }

    return JsonResponse(context)


@dataclass
class SearchFields:
    query: str
    birthday: Optional[str] = None
    badge_ids: Optional[List[int]] = None

    @classmethod
    def parse(cls, query: str) -> "SearchFields":
        badge_nums = re.search(r"num:([0-9,]+)", query)
        if badge_nums:
            try:
                badge_ids = [int(num) for num in badge_nums.group(1).split(",")]
                return SearchFields(badge_ids=badge_ids, query="")
            except ValueError:
                query = query.replace(badge_nums.group(0), "")

        birthday = re.search(r"birthday:([0-9-]{10}) ?", query)
        if birthday:
            query = query.replace(birthday.group(0), "")
            birthday = birthday.group(1)

        query = query.strip()

        return SearchFields(query=query, birthday=birthday)


@require_safe
@staff_or_terminal_required()
def onsite_admin_search(request):
    event = Event.objects.get(default=True)
    query = request.GET.get("search", None)
    if query is None:
        return redirect("registration:onsite_admin")

    data = []

    def collect_badges(badges):
        for badge in badges:
            data.append(
                {
                    "id": badge.id,
                    "editUrl": reverse(
                        "admin:registration_badge_change", args=(badge.id,)
                    ),
                    "attendee": {
                        "firstName": badge.attendee.firstName,
                        "lastName": badge.attendee.lastName,
                        "preferredName": badge.attendee.preferredName,
                        "dob": badge.attendee.birthdate,
                    },
                    "badgeName": badge.badgeName,
                    "badgeNumber": badge.badgeNumber,
                    "abandoned": badge.abandoned,
                }
            )

    query = query.strip()

    fields = SearchFields.parse(query)

    if fields.badge_ids:
        badges = Badge.objects.filter(event=event, badgeNumber__in=fields.badge_ids)
        collect_badges(badges)

    full_name = Func(
        F("attendee__firstName"), Value(" "), F("attendee__lastName"), function="CONCAT"
    )
    greater_similarity = Func(
        "name_similarity", "badge_similarity", function="GREATEST"
    )

    filters = (
        Q(name_similarity__gte=0.4)
        | Q(badge_similarity__gte=0.6)
        | Q(attendee__lastName__iexact=fields.query)
    )

    if fields.birthday:
        filters = filters & Q(attendee__birthdate=fields.birthday)

    results = (
        Badge.objects.annotate(
            name_similarity=TrigramSimilarity(full_name, fields.query),
            badge_similarity=TrigramSimilarity("badgeName", fields.query),
        )
        .filter(Q(event=event) & filters)
        .order_by(greater_similarity)
        .reverse()
        .prefetch_related("attendee")[:50]
    )

    collect_badges(results)

    return JsonResponse({"success": True, "results": data})


def parse_badge_id_params(request):
    try:
        return [int(badge_id) for badge_id in request.GET.getlist("id")], None
    except ValueError:
        return None, JsonResponse(
            {"success": False, "reason": "Unexpected badge ID value"}, status=400
        )


def send_mqtt_message_to_terminal(
    terminal: Firebase, topic: str, data={}
) -> JsonResponse:
    topic = mqtt.get_topic(topic, name=str(terminal.name))

    try:
        mqtt.send_mqtt_message(topic, data)
    except Exception:
        logger.exception("Could not send MQTT message", extra={"topic": topic})
        return JsonResponse(
            {"success": False, "reason": "Could not send MQTT message"}, status=500
        )

    return JsonResponse({"success": True})


def load_json_body(request) -> dict:
    try:
        body = json.loads(request.body or b"{}")
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def extract_badge_ids(values) -> List[int]:
    result = []
    for value in values or []:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            continue
    return result


def get_cart_orders(badges) -> List[Order]:
    orders_by_id = {}
    for badge in badges:
        order = badge.getOrder()
        if order is not None:
            orders_by_id.setdefault(order.id, order)
    return list(orders_by_id.values())


def unify_order_references(badges) -> Optional[str]:
    orders = get_cart_orders(badges)
    if not orders:
        return None

    first_reference = orders[0].reference
    for order in orders[1:]:
        if order.reference != first_reference:
            order.reference = first_reference
            order.save()
    return first_reference


def push_cart_to_terminal(terminal: Firebase, data: dict) -> None:
    terminal_data = {
        "badges": [
            {
                "id": badge["id"],
                "firstName": badge["firstName"],
                "lastName": badge["lastName"],
                "badgeName": badge["badgeName"],
                "effectiveLevel": {
                    "name": badge["effectiveLevel"]["name"],
                    "price": str(badge["level_subtotal"]),
                },
                "discountedPrice": str(badge["level_total"]),
            }
            for badge in data["result"]
        ],
        "charityDonation": str(data["charityDonation"]),
        "organizationDonation": str(data["orgDonation"]),
        "totalDiscount": str(data["total_discount"]),
        "total": str(data["total"]),
        "paid": str(data["paid"]),
    }

    send_mqtt_message_to_terminal(terminal, "payment/cart/update", terminal_data)


@require_POST
@staff_or_terminal_required(require_terminal=True)
def enable_payment(request: RequiredTerminalRequest):
    badge_ids = extract_badge_ids(load_json_body(request).get("badge_ids"))
    if not badge_ids:
        return JsonResponse(
            {"success": False, "reason": "Cart not initialized or empty"}, status=400
        )

    terminal = request.terminal

    badges = list(Badge.objects.filter(id__in=badge_ids))
    unify_order_references(badges)

    data = build_result(badge_ids)

    push_cart_to_terminal(terminal, data)

    order_id = payments.create_square_order(str(terminal.name), data)

    if (
        terminal.payment_type == Firebase.SQUARE_TERMINAL
        or request.GET.get("fallback", None) == "true"
    ) and terminal.square_terminal_id:
        api_response = payments.prompt_terminal_payment(
            request,
            str(terminal.square_terminal_id),
            int(data["total"] * 100),
            data["reference"],
            render_to_string("registration/customer-note.txt", data),
            order_id,
        )

        if api_response.checkout:
            return JsonResponse(
                {
                    "success": True,
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "reason": ", ".join(
                        [str(error.detail) for error in api_response.errors or []]
                    ),
                }
            )
    elif terminal.payment_type == Firebase.MQTT_REGISTER_APP:
        return send_mqtt_message_to_terminal(
            terminal,
            "payment/process",
            {
                "paymentAttemptId": payments.get_idempotency_key(request),
                "orderId": order_id,
                "total": int(data["total"] * 100),
                "reference": data["reference"],
                "note": render_to_string("registration/customer-note.txt", data),
            },
        )
    else:
        return JsonResponse(
            {
                "success": False,
                "reason": "Terminal does not have payment type",
            }
        )


@require_POST
@staff_or_terminal_required()
def assign_badge_number(request):
    request_badges = json.loads(request.body)

    badge_payload = {badge["id"]: badge for badge in request_badges}

    badge_set = Badge.objects.filter(id__in=list(badge_payload.keys()))

    admin.assign_badge_numbers(None, request, badge_set)
    errors = get_messages_list(request)
    if errors:
        return JsonResponse(
            {"success": False, "errors": errors, "reason": "\n".join(errors)},
            status=400,
        )
    return JsonResponse({"success": True})


def get_messages_list(request):
    storage = get_messages(request)
    return [message.message for message in storage]


@require_POST
@staff_or_terminal_required()
def onsite_print_badges(request: TerminalRequest):
    badge_list = request.GET.getlist("id")
    terminal = request.terminal

    signer = TimestampSigner()
    data = signer.sign_object(
        {
            "badge_ids": [int(badge_id) for badge_id in badge_list],
            "terminal": terminal.name if terminal else None,
            "source": PrintHistory.ONSITE,
        }
    )

    pdf_path = reverse("registration:pdf") + f"?data={data}"
    print_url = reverse("registration:print") + "?" + urlencode({"file": pdf_path})

    return JsonResponse(
        {
            "success": True,
            "next": request.get_full_path(),
            "file": pdf_path,
            "url": print_url,
        }
    )


def admin_push_cart_refresh(request: TerminalRequest):
    if request.terminal:
        send_mqtt_message_to_terminal(request.terminal, "web/refresh")


# TODO: update for square SDK data type (fetch txn from square API and store in order.apiData)
@require_POST
@device_token_required()
def complete_square_transaction(request: TerminalRequest):
    data = json.loads(request.body)

    reference = data.get("reference")
    paymentId = data.get("paymentId")

    if not reference or not paymentId:
        return JsonResponse(
            {
                "success": False,
                "reason": "reference and transactionId are required parameters",
            },
            status=400,
        )

    # Things we need:
    #   orderID or reference (passed to square by metadata)
    # Square returns:
    #   clientTransactionId (offline payments)
    #   serverTransactionId (online payments)

    orders = list(Order.objects.filter(reference=reference).prefetch_related())
    if not orders:
        logger.error("No order matching reference", extra={"reference": reference})
        return JsonResponse(
            {
                "success": False,
                "reason": "No order matching the reference specified exists",
            },
            status=404,
        )

    combine_orders(orders)

    store_api_data = {}

    order = orders[0]
    order.billingType = Order.CREDIT

    # Lookup the payment(s?) associated with this order:
    if paymentId:
        store_api_data["payment"] = {"id": paymentId}
        order.status = Order.COMPLETED
        order.settledDate = timezone.now()
    else:
        order.status = Order.CAPTURED
        order.notes = "No paymentId."

    order.status = Order.COMPLETED
    order.settledDate = timezone.now()

    order.apiData = json.dumps(store_api_data)
    order.save()

    if paymentId:
        status, errors = payments.refresh_payment(order, store_api_data)
        if not status:
            return JsonResponse({"success": False, "error": errors}, status=210)

    admin_push_cart_refresh(request)

    return JsonResponse({"success": True})


def combine_orders(orders):
    # If there is more than one order, we should flatten them into one by reassigning all these
    # orderItems to the first order, and delete the rest.
    first_order = orders[0]

    if len(orders) > 1:
        order_items = []

        for order in orders[1:]:
            order_items += order.orderitem_set.all()
            first_order.notes += (
                f"\n[Combined from order reference {order.reference}]\n{order.notes}\n"
            )

        for order_item in order_items:
            old_order = order_item.order
            order_item.order = first_order
            if old_order and old_order.id:
                logger.warning(
                    "Deleting old order during combine",
                    extra={"order_id": old_order.id},
                )
                old_order.delete()
            order_item.save()

        first_order.save()


@require_safe
@staff_member_required
@permission_required("order.cash_admin")
def drawer_status(request):
    if Cashdrawer.objects.count() == 0:
        return JsonResponse({"success": False})
    total = Cashdrawer.objects.all().aggregate(Sum("total"))
    drawer_total = Decimal(total["total__sum"])
    if drawer_total == 0:
        status = "CLOSED"
    elif drawer_total < 0:
        status = "SHORT"
    elif drawer_total > 0:
        status = "OPEN"
    return JsonResponse({"success": True, "total": drawer_total, "status": status})


@require_POST
@staff_member_required
@permission_required("order.cash_admin")
def no_sale(request):
    position = resolve_terminal_from_request(request)
    if position is None:
        return no_terminal_response()
    mqtt.send_mqtt_message(mqtt.get_topic("receipt/nosale", name=str(position.name)))

    return JsonResponse({"success": True})


def print_audit_receipt(request, position, audit_type, cash_ledger, cashdraw=True):
    event = Event.objects.get(default=True)
    payload = {
        "v": 1,
        "event": event.name,
        "terminal": position.name,
        "type": audit_type,
        "amount": abs(cash_ledger.total),
        "user": request.user.username,
        "timestamp": cash_ledger.timestamp.isoformat(),
        "cashdraw": cashdraw,
    }

    mqtt.send_mqtt_message(
        mqtt.get_topic("receipt/auditslip", name=str(position.name)), payload
    )


def cash_audit_action(request, action):
    cashdraw = True
    amount = Decimal(request.POST.get("amount", None))
    position = resolve_terminal_from_request(request)
    if position is None:
        return no_terminal_response()
    if action in (Cashdrawer.DROP, Cashdrawer.PICKUP, Cashdrawer.CLOSE):
        amount = -abs(amount)
        cashdraw = False
    cash_ledger = Cashdrawer(
        action=action, total=amount, user=request.user, position=position
    )
    cash_ledger.save()
    cash_ledger.refresh_from_db()
    print_audit_receipt(request, position, action, cash_ledger, cashdraw)

    return JsonResponse({"success": True})


@require_POST
@staff_member_required
@permission_required("order.cash_admin")
def open_drawer(request):
    return cash_audit_action(request, Cashdrawer.OPEN)


@require_POST
@staff_member_required
@permission_required("order.cash_admin")
def cash_deposit(request):
    return cash_audit_action(request, Cashdrawer.DEPOSIT)


@require_POST
@staff_member_required
@permission_required("order.cash_admin")
def safe_drop(request):
    return cash_audit_action(request, Cashdrawer.DROP)


@require_POST
@staff_member_required
@permission_required("order.cash_admin")
def cash_pickup(request):
    return cash_audit_action(request, Cashdrawer.PICKUP)


@require_POST
@staff_member_required
@permission_required("order.cash_admin")
def close_drawer(request):
    return cash_audit_action(request, Cashdrawer.CLOSE)


def cash_receipt_payload(order: Order, tendered: str, total: str) -> dict:
    order_items = OrderItem.objects.filter(order=order)
    attendee_options = []
    for item in order_items:
        attendee_options.extend(get_line_items(item.attendeeoptions_set.all()))

    # discounts
    if order.discount:
        if order.discount.amountOff:
            attendee_options.append(
                {"item": "Discount", "price": "-${0}".format(order.discount.amountOff)}
            )
        elif order.discount.percentOff:
            attendee_options.append(
                {"item": "Discount", "price": "-%{0}".format(order.discount.percentOff)}
            )

    event = Event.objects.get(default=True)
    payload = {
        "v": 1,
        "event": event.name,
        "line_items": attendee_options,
        "donations": {"org": {"name": event.name, "price": str(order.orgDonation)}},
        "total": order.total,
        "payment": {
            "type": order.billingType,
            "tendered": Decimal(tendered),
            "change": Decimal(tendered) - Decimal(total),
            "details": "Ref: {0}".format(order.reference),
        },
        "reference": order.reference,
    }

    if event.charity:
        payload["donations"]["charity"] = (
            {"name": event.charity.name, "price": str(order.charityDonation)},
        )

    return payload


@require_POST
@staff_or_terminal_required(("order.cash",))
def complete_cash_transaction(request: TerminalRequest):
    body = load_json_body(request)

    badge_ids = extract_badge_ids(body.get("badge_ids"))
    tendered = body.get("tendered", None)

    if not badge_ids or tendered is None:
        return JsonResponse(
            {
                "success": False,
                "reason": "badge_ids and tendered are required parameters",
            },
            status=400,
        )

    badges = list(Badge.objects.filter(id__in=badge_ids))
    if not badges:
        return JsonResponse(
            {"success": False, "reason": "No matching badges exist"}, status=404
        )

    data = build_result([badge.id for badge in badges])
    total = Decimal(data["total"]).quantize(TWOPLACES)
    try:
        tendered = Decimal(str(tendered)).quantize(TWOPLACES)
    except (InvalidOperation, TypeError):
        return JsonResponse(
            {"success": False, "reason": "Invalid tendered amount"}, status=400
        )
    change = tendered - total
    if change < 0:
        return JsonResponse(
            {"success": False, "reason": "Tendered amount is less than the total"},
            status=400,
        )

    orders = get_cart_orders(badges)
    if not orders:
        return JsonResponse(
            {"success": False, "reason": "No matching orders exist"}, status=404
        )

    with transaction.atomic():
        combine_orders(orders)

        order = orders[0]
        order.billingType = Order.CASH
        order.status = Order.COMPLETED
        order.settledDate = timezone.now()
        order.notes = json.dumps({"type": "cash", "tendered": str(tendered)})
        order.save()

        Cashdrawer(
            action=Cashdrawer.TRANSACTION,
            total=total,
            tendered=tendered,
            user=None if request.terminal_authed else request.user,
            position=request.terminal,
        ).save()

    payload = cash_receipt_payload(order, str(tendered), str(total))

    terminal = request.terminal
    if terminal:
        mqtt.send_mqtt_message(
            mqtt.get_topic("receipt/print/cash", name=str(terminal.name)), payload
        )

    return JsonResponse({"success": True, "total": total, "change": change})


def get_discount_dict(discount):
    if discount:
        reason = "\n\n---\n\n".join(filter(None, [discount.reason, discount.notes]))

        return {
            "name": discount.codeName,
            "percent_off": discount.percentOff,
            "amount_off": discount.amountOff,
            "id": discount.id,
            "valid": discount.isValid(),
            "status": discount.status,
            "reason": reason,
        }

    return None


def get_line_items(attendee_options: Iterable[AttendeeOptions]):
    out = []
    for option in attendee_options:
        option_dict = {
            "id": option.id,
            "item": option.option.optionName,
            "price": option.option.optionPrice,
            "quantity": 1,
            "total": option.option.optionPrice,
            "optionExtraType": option.option.optionExtraType,
            "optionValue": option.optionValue,
            "requiresFulfillment": option.option.requires_fulfillment,
            "fulfilledAt": option.fulfilled_at,
        }

        if option.option.optionExtraType == "int":
            val = Decimal(option.optionValue)
            option_dict["quantity"] = int(val)
            option_dict["total"] = option.option.optionPrice * val

        out.append(option_dict)
    return out


def build_result(cart):
    badges = []
    for pk in list(cart):
        try:
            badge = Badge.objects.get(id=pk)
            badges.append(badge)
        except Badge.DoesNotExist:
            logger.error(
                "ID {0} was in cart but doesn't exist in the database".format(pk)
            )

    order = None
    subtotal = Decimal(0)
    total_discount = Decimal(0)
    result = []
    orders = set()
    included_badges = []
    for badge in badges:
        order = badge.getOrder()
        if order is None:
            logger.warning(
                "ID {0} was in cart but has no order".format(badge.id),
            )
            continue

        included_badges.append(badge)
        orders.add(order)

        oi = badge.getOrderItems()
        level = None
        level_subtotal = 0
        attendee_options = []
        effectiveLevel = None
        for item in oi:
            level = item.priceLevel
            attendee_options.extend(get_line_items(item.getOptions()))
            level_subtotal += get_order_item_option_total(item.getOptions())

            if level:
                effectiveLevel = {"name": level.name, "price": level.basePrice}
                level_subtotal += level.basePrice

        subtotal += level_subtotal

        holdType = None
        if badge.attendee.holdType:
            holdType = badge.attendee.holdType.name

        level_discount = (
            Decimal(get_discount_total(order.discount, level_subtotal) * 100)
            * TWOPLACES
        )
        total_discount += level_discount

        staff_data = None

        if badge.abandoned == Badge.STAFF:
            staff = Staff.objects.get(event=badge.event, attendee=badge.attendee)

            staff_data = {
                "shirtSize": staff.shirtsize.name if staff.shirtsize else None,
                "beforeDeadline": order.createdDate <= badge.event.staffRegEnd,
            }

        item = {
            "id": badge.id,
            "orderId": order.id,
            "firstName": badge.attendee.preferredName or badge.attendee.firstName,
            "lastName": badge.attendee.lastName,
            "badgeName": badge.badgeName,
            "badgeNumber": badge.badgeNumber,
            "abandoned": badge.abandoned,
            "eventId": badge.event_id,
            "effectiveLevel": effectiveLevel,
            "discount": get_discount_dict(order.discount),
            "age": get_attendee_age(badge.attendee),
            "holdType": holdType,
            "level_subtotal": level_subtotal,
            "level_discount": level_discount,
            "level_total": level_subtotal - level_discount,
            "attendee_options": attendee_options,
            "printed": badge.printed,
            "reference": order.reference,
            "staff": staff_data,
        }
        result.append(item)

    total = subtotal
    paid = Decimal(0)

    charityDonation = Decimal(0)
    orgDonation = Decimal(0)

    for order in orders:
        total += order.orgDonation + order.charityDonation
        paid += (
            order.total
            if order.billingType != Order.UNPAID
            and order.status in (Order.CAPTURED, Order.COMPLETED)
            else 0
        )

        charityDonation += order.charityDonation
        orgDonation += order.orgDonation

    data = {
        "success": True,
        "result": result,
        "badge_ids": [badge.id for badge in included_badges],
        "subtotal": subtotal,
        "total": total - total_discount,
        "total_discount": total_discount,
        "charityDonation": charityDonation,
        "orgDonation": orgDonation,
        "paid": paid,
    }

    if order is not None:
        data["order_id"] = order.id
        data["reference"] = order.reference
    else:
        data["order_id"] = None
        data["reference"] = None

    return data


@require_safe
@staff_or_terminal_required()
def onsite_admin_cart(request: TerminalRequest):
    badge_ids, error = parse_badge_id_params(request)
    if error:
        return error

    data = build_result(badge_ids)

    if request.terminal:
        if badge_ids:
            push_cart_to_terminal(request.terminal, data)
        else:
            send_mqtt_message_to_terminal(request.terminal, "payment/cart/clear")

    return JsonResponse(data)


@require_safe
@staff_or_terminal_required()
def onsite_cart_expand(request):
    badge_ids, error = parse_badge_id_params(request)
    if error:
        return error

    badges = Badge.objects.filter(id__in=badge_ids)
    if len(badge_ids) > 1:
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(badge_ids)])
        badges = badges.order_by(preserved)

    expanded: List[int] = []
    for badge in badges:
        order_item = OrderItem.objects.filter(badge=badge, order__isnull=False).first()
        if order_item:
            order_items = OrderItem.objects.filter(
                order=order_item.order, badge__isnull=False
            )
            for order_item in order_items:
                if order_item.badge_id not in expanded:
                    expanded.append(order_item.badge_id)

    return JsonResponse({"success": True, "badge_ids": expanded})


@require_POST
@staff_or_terminal_required()
def onsite_admin_transfer_cart(request):
    terminal_id = request.GET.get("terminal_id")
    badge_ids = request.GET.getlist("badge_id")

    firebase = Firebase.objects.get(id=terminal_id)

    topic = mqtt.get_topic("web/transfer", name=str(firebase.name))
    mqtt.send_mqtt_message(
        topic,
        {
            "badgeIds": [int(badge_id) for badge_id in badge_ids],
        },
    )

    return JsonResponse({"success": True})


def get_b32_uuid():
    uid = base64.b32encode(uuid.uuid4().bytes).decode("ascii")
    return uid[:26]


@require_POST
@staff_or_terminal_required(("order.discount",))
def create_discount(request: TerminalRequest):
    body = load_json_body(request)

    discount_type = body.get("type")
    notes = body.get("notes") or None
    department = None
    if department_id := body.get("department") or None:
        department = Department.objects.get(id=int(department_id))

    try:
        value = Decimal(str(body.get("value")))
    except (InvalidOperation, TypeError):
        return JsonResponse({"success": False, "reason": "Unknown value provided"})

    badge_ids = extract_badge_ids(body.get("badge_ids"))
    if not badge_ids:
        return JsonResponse(
            {"success": False, "reason": "Cart not initialized or empty"}, status=400
        )

    amount_off = Decimal(0)
    percent_off = Decimal(0)

    match discount_type:
        case "Amount":
            amount_off = value
        case "Percent":
            percent_off = value

    if request.terminal_authed:
        attribution = f"terminal [{request.terminal.name}]"
    else:
        attribution = f"[{request.user}]"

    notes = "\n\n".join(
        item for item in [notes, f"Applied by {attribution}"] if item is not None
    )

    orders = get_cart_orders(Badge.objects.filter(pk__in=badge_ids))

    if not orders:
        return JsonResponse(
            {"success": False, "reason": "Cart has no orders"}, status=400
        )

    with transaction.atomic():
        discount = Discount(
            codeName=generate_discount_code(),
            percentOff=percent_off,
            amountOff=amount_off,
            startDate=timezone.now(),
            endDate=timezone.now() + timedelta(hours=1),
            notes=notes,
            oneTime=True,
            used=0,
            reason="Onsite admin discount",
            sponsoring_department=department,
        )
        discount.save()

        combine_orders(orders)

        order = orders[0]
        order.discount = discount
        order.save()

        data = build_result(badge_ids)
        if data["total"] <= 0 and order.billingType == Order.UNPAID:
            complete_comp_order(order, discount)

    return JsonResponse({"success": True})


@require_POST
@staff_or_terminal_required()
def onsite_print_clear(request):
    id = request.GET.get("id", None)
    if id is None or id == "":
        return JsonResponse(
            {"success": False, "reason": "Need ID parameter"}, status=400
        )

    try:
        id = int(id)
    except ValueError:
        return JsonResponse(
            {"success": False, "reason": "ID parameter must be integer"}, status=400
        )

    badge = Badge.objects.get(id=id)
    badge.printed = False
    badge.save()

    return JsonResponse({"success": True})


@require_POST
@staff_or_terminal_required(require_terminal=True)
def regtoken(request: RequiredTerminalRequest):
    signer = TimestampSigner()
    data = signer.sign_object(
        {
            "terminal": request.terminal.name,
        }
    )

    return JsonResponse({"success": True, "token": data})


@require_safe
@staff_or_terminal_required()
def attendee_details(request):
    id = request.GET.get("id", None)
    if id is None or id == "":
        return JsonResponse(
            {"success": False, "reason": "Need ID parameter"}, status=400
        )

    try:
        id = int(id)
    except ValueError:
        return JsonResponse(
            {"success": False, "reason": "ID parameter must be integer"}, status=400
        )

    attendee = Badge.objects.get(id=id).attendee

    return JsonResponse(
        {
            "success": True,
            "attendee": {
                "firstName": attendee.firstName,
                "lastName": attendee.lastName,
                "preferredName": attendee.preferredName,
                "email": attendee.email,
                "phone": attendee.phone,
                "address1": attendee.address1,
                "address2": attendee.address2,
                "city": attendee.city,
                "state": attendee.state,
                "country": attendee.country,
                "postalCode": attendee.postalCode,
                "dob": attendee.birthdate,
            },
        }
    )


def _square_oauth_cache_key(state: str) -> str:
    return f"square_oauth_state:{state}"


@device_token_required(require_terminal=True)
def terminal_square_token(request: RequiredTerminalRequest):
    terminal = request.terminal

    base_url = "https://connect.squareup.com"
    if settings.SQUARE_ENVIRONMENT == "sandbox":
        base_url = "https://connect.squareupsandbox.com"

    scopes = ["MERCHANT_PROFILE_READ", "PAYMENTS_WRITE", "PAYMENTS_WRITE_IN_PERSON"]
    state = get_random_token(64)

    cache.set(_square_oauth_cache_key(state), terminal.id, timeout=600)

    url = f"{base_url}/oauth2/authorize?client_id={settings.SQUARE_APPLICATION_ID}&state={state}&scope={'+'.join(scopes)}"

    send_mqtt_message_to_terminal(
        terminal,
        "web/authorize/square",
        {
            "url": url,
            "state": state,
        },
    )

    return JsonResponse(True, safe=False)


@require_safe
def oauth_square(request):
    url_state = request.GET.get("state")

    terminal = None
    if url_state:
        terminal_id = cache.get(_square_oauth_cache_key(url_state))
        if terminal_id:
            terminal = Firebase.objects.filter(id=terminal_id).first()

    if not terminal:
        return JsonResponse(
            {"success": False, "reason": "Unknown or expired OAuth state"},
            status=400,
        )

    code = request.GET.get("code")
    if not code:
        reason = request.GET.get("error") or "No authorization code provided"
        return JsonResponse({"success": False, "reason": reason}, status=400)

    try:
        token = payments.client.o_auth.obtain_token(
            client_id=settings.SQUARE_APPLICATION_ID,
            client_secret=settings.SQUARE_APPLICATION_SECRET,
            grant_type="authorization_code",
            code=code,
        )
    except Exception:
        logger.exception("Could not exchange Square authorization code")
        return JsonResponse(
            {
                "success": False,
                "reason": "Could not exchange Square authorization code",
            },
            status=400,
        )

    cache.delete(_square_oauth_cache_key(url_state))

    send_mqtt_message_to_terminal(
        terminal,
        "payment/update/token",
        {
            "accessToken": token.access_token,
            "refreshToken": token.refresh_token,
        },
    )

    resp = HttpResponseRedirect(reverse("registration:onsite_admin"))
    return resp


@require_POST
@staff_or_terminal_required(require_terminal=True)
def print_receipts(request: RequiredTerminalRequest):
    terminal = request.terminal

    references = request.GET.getlist("reference", [])
    orders = Order.objects.filter(reference__in=references).prefetch_related()

    for order in orders:
        if order.billingType in (Order.UNPAID, Order.COMP):
            continue

        if order.billingType == Order.CASH:
            try:
                note_data = json.loads(order.notes)
            except:
                logger.warning(
                    "Cash order missing note data for receipt reprint",
                    extra={"order_id": order.id},
                )
                return JsonResponse(
                    {"success": False, "reason": "Cash order was missing note data"}
                )

            payload = cash_receipt_payload(order, note_data["tendered"], order.total)
            topic = mqtt.get_topic("receipt/print/cash", name=str(terminal.name))
            mqtt.send_mqtt_message(topic, payload)

        elif order.billingType == Order.CREDIT:
            if not order.apiData or "payment" not in order.apiData:
                return JsonResponse(
                    {
                        "success": False,
                        "reason": "Missing payment data on credit transaction",
                    }
                )

            if not payments.print_payment_receipt(
                request, terminal.square_terminal_id, order.apiData["payment"]["id"]
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "reason": "Got error attempting to print receipt",
                    }
                )

    return JsonResponse({"success": True})


@require_POST
@staff_or_terminal_required()
def fulfill(request: TerminalRequest):
    attendee_option_id = request.POST.get("id")

    with transaction.atomic():
        try:
            attendee_option = (
                AttendeeOptions.objects.select_for_update()
                .filter(pk=attendee_option_id)
                .first()
            )
        except AttendeeOptions.DoesNotExist:
            return JsonResponse({"success": False, "reason": "Option ID is unknown"})

        if attendee_option.fulfilled_at:
            return JsonResponse(
                {"success": False, "reason": "Option was already fulfilled"}
            )

        if not attendee_option.option.requires_fulfillment:
            return JsonResponse(
                {"success": False, "reason": "Option does not require fulfillment"}
            )

        if attendee_option.orderItem.badge.effectiveLevel() == Badge.UNPAID:
            return JsonResponse(
                {
                    "success": False,
                    "reason": "Option cannot be fulfilled for unpaid order",
                }
            )

        attendee_option.fulfilled_at = timezone.now()
        attendee_option.fulfilled_by = None if request.terminal_authed else request.user
        attendee_option.save()

    return JsonResponse({"success": True})


@require_safe
@staff_member_required
def onsite_admin_badge_history(request):
    badge_id = request.GET.get("id")
    try:
        badge = Badge.objects.get(id=int(badge_id))
    except (TypeError, ValueError, Badge.DoesNotExist):
        return JsonResponse({"success": False, "reason": "Badge not found"})

    source_labels = dict(PrintHistory.SOURCE_CHOICES)
    print_history = badge.printhistory_set.select_related("firebase").order_by(
        "created_at"
    )
    roll_history = badge.roll_forwards.select_related(
        "from_event", "to_event", "rolled_by"
    ).order_by("rolled_at")

    return JsonResponse(
        {
            "success": True,
            "printHistory": [
                {
                    "source": source_labels.get(h.source, h.source),
                    "terminal": h.firebase.name if h.firebase else None,
                    "printedAt": h.created_at.isoformat(),
                }
                for h in print_history
            ],
            "rollHistory": [
                {
                    "fromEvent": h.from_event.name,
                    "toEvent": h.to_event.name,
                    "rolledAt": h.rolled_at.isoformat(),
                    "rolledBy": h.rolled_by.username if h.rolled_by else None,
                }
                for h in roll_history
            ],
        }
    )


@require_POST
@staff_member_required
def onsite_admin_badge_edit(request):
    badge_id = request.GET.get("id")
    badge_name = request.GET.get("badge_name")
    event_id = request.GET.get("event_id")

    try:
        badge = Badge.objects.get(id=int(badge_id))
    except (TypeError, ValueError, Badge.DoesNotExist):
        return JsonResponse({"success": False, "reason": "Badge not found"})

    if badge_name is not None:
        badge.badgeName = badge_name

    if event_id is not None:
        try:
            to_event = Event.objects.get(id=int(event_id))
        except (ValueError, Event.DoesNotExist):
            return JsonResponse({"success": False, "reason": "Event not found"})

        if badge.event_id != to_event.id:
            try:
                badge.roll_forward(to_event, rolled_by=request.user)
            except ValueError:
                return JsonResponse(
                    {"success": False, "reason": "Could not roll forward"}
                )

            # Roll forward already saves the object so don't save again.
            return JsonResponse({"success": True})

    badge.save()
    return JsonResponse({"success": True})
