import base64
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Iterable, List, Optional, Union

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.contrib.messages import get_messages
from django.contrib.postgres.search import TrigramSimilarity
from django.core.signing import TimestampSigner
from django.db import transaction
from django.db.models import Case, F, Func, Q, Sum, Value, When
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt
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
from registration.views.common import logger
from registration.views.ordering import (
    get_discount_total,
    get_order_item_option_total,
)


def flatten(l):
    return [item for sublist in l for item in sublist]


logger = logging.getLogger(__name__)

TWOPLACES = Decimal(10) ** -2


def get_active_terminal(request) -> Optional[Firebase]:
    term_id = request.session.get("terminal")
    if term_id:
        try:
            return Firebase.objects.get(pk=int(term_id))
        except Firebase.DoesNotExist:
            return None
    return None


@require_safe
@staff_member_required
def onsite_admin(request):
    # Modify a dummy session variable to keep it alive
    request.session["heartbeat"] = time.time()

    get_terminal_from_request(request)

    return render(request, "registration/spa-host.html")


@require_safe
@staff_member_required
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
        request.session["terminal"] = terminal.id

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
@staff_member_required
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


def update_terminal_status(request, status: str) -> JsonResponse:
    active = get_terminal_from_request(request)
    if not active:
        return JsonResponse(
            {"success": False, "reason": "No terminal associated with request"},
            status=400,
        )

    return send_mqtt_message_to_terminal(
        active,
        "payment/state",
        status,
    )


@require_POST
@staff_member_required
def set_terminal_status(request):
    status = request.GET.get("status", "close")
    return update_terminal_status(request, status)


def get_terminal_from_request(request) -> Optional[Firebase]:
    url_terminal = request.GET.get("terminal", None)
    session_terminal = request.session.get("terminal", None)

    active = None

    if url_terminal:
        try:
            active = Firebase.objects.get(id=int(url_terminal))
            request.session["terminal"] = active.id
        except (ValueError, Firebase.DoesNotExist):
            return None

    if not active and session_terminal:
        try:
            active = Firebase.objects.get(id=int(session_terminal))
        except Firebase.DoesNotExist:
            return None

    return active


def send_mqtt_message_to_terminal(
    request: Union[HttpRequest, Firebase], topic: str, data={}
) -> JsonResponse:
    if isinstance(request, Firebase):
        active = request
    else:
        active = get_terminal_from_request(request)
        if not active:
            return JsonResponse(
                {"sucess": False, "reason": "No terminal associated with request"},
                status=400,
            )

    topic = mqtt.get_topic(topic, name=str(active.name))

    try:
        mqtt.send_mqtt_message(topic, data)
    except Exception as ex:
        logger.error("could not send mqtt message: %s", ex)
        return JsonResponse(
            {"success": False, "reason": "Could not send MQTT message"}, status=500
        )

    return JsonResponse({"success": True})


@require_POST
@staff_member_required
def enable_payment(request):
    cart = request.session.get("cart", None)
    if cart is None:
        request.session["cart"] = []
        return JsonResponse(
            {"success": False, "reason": "Cart not initialized"}, status=200
        )

    badges = []
    first_order = None

    for pk in cart:
        try:
            badge = Badge.objects.get(id=pk)
            badges.append(badge)

            order = badge.getOrder()
            if first_order is None:
                first_order = order
            else:
                # FIXME: use order.onsite_reference instead.
                # FIXME: Put this in cash handling, too
                # Reassign order references of items in cart to match first:
                order = badge.getOrder()
                order.reference = first_order.reference
                order.save()
        except Badge.DoesNotExist:
            cart.remove(pk)
            logger.error(
                "ID {0} was in cart but doesn't exist in the database".format(pk)
            )

    # Force a cart refresh to get the latest order reference to the terminal
    onsite_admin_cart(request)

    data = build_result(cart)

    terminal = get_terminal_from_request(request)
    if not terminal:
        return JsonResponse(
            {"sucess": False, "reason": "No terminal associated with request."}
        )

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
@staff_member_required
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
@staff_member_required
def onsite_print_badges(request):
    badge_list = request.GET.getlist("id")
    terminal = get_active_terminal(request)

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


def admin_push_cart_refresh(request):
    send_mqtt_message_to_terminal(request, "web/refresh")


# TODO: update for square SDK data type (fetch txn from square API and store in order.apiData)
@csrf_exempt
def complete_square_transaction(request):
    try:
        token = request.headers.get("authorization").removeprefix("Bearer ")
    except:
        return JsonResponse(
            {"success": False, "reason": "Invalid authorization"}, status=401
        )

    try:
        terminal = Firebase.objects.get(token=token)
        request.session["terminal"] = terminal.id
    except Firebase.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "reason": "Unknown token",
            },
            status=401,
        )

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

    try:
        orders = Order.objects.filter(reference=reference).prefetch_related()
    except Order.DoesNotExist:
        logger.error("No order matching reference {0}".format(reference))
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
                logger.warning("Deleting old order id={0}".format(old_order.id))
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
    position = get_active_terminal(request)
    mqtt.send_mqtt_message(mqtt.get_topic("receipt/nosale", name=str(position.name)))

    return JsonResponse({"success": True})


@staff_member_required
@permission_required("order.cash_admin")
def print_audit_receipt(request, audit_type, cash_ledger, cashdraw=True):
    position = get_active_terminal(request)
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
    position = get_active_terminal(request)
    if action in (Cashdrawer.DROP, Cashdrawer.PICKUP, Cashdrawer.CLOSE):
        amount = -abs(amount)
        cashdraw = False
    cash_ledger = Cashdrawer(
        action=action, total=amount, user=request.user, position=position
    )
    cash_ledger.save()
    cash_ledger.refresh_from_db()
    print_audit_receipt(request, action, cash_ledger, cashdraw)

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
@staff_member_required
@permission_required("order.cash")
def complete_cash_transaction(request):
    reference = request.GET.get("reference", None)
    total = request.GET.get("total", None)
    tendered = request.GET.get("tendered", None)

    if reference is None or tendered is None or total is None:
        return JsonResponse(
            {
                "success": False,
                "reason": "Reference, tendered, and total are required parameters",
            },
            status=400,
        )

    try:
        orders = Order.objects.filter(reference=reference).prefetch_related()
    except Order.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "reason": "No order matching the reference specified exists",
            },
            status=404,
        )

    combine_orders(orders)

    order = orders[0]
    order.billingType = Order.CASH
    order.status = Order.COMPLETED
    order.settledDate = timezone.now()
    order.notes = json.dumps({"type": "cash", "tendered": tendered})
    order.save()

    txn = Cashdrawer(
        action=Cashdrawer.TRANSACTION, total=total, tendered=tendered, user=request.user
    )
    txn.save()

    payload = cash_receipt_payload(order, tendered, total)

    terminal = get_active_terminal(request)
    mqtt.send_mqtt_message(
        mqtt.get_topic("receipt/print/cash", name=str(terminal.name)), payload
    )

    return JsonResponse({"success": True})


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
    for pk in cart:
        try:
            badge = Badge.objects.get(id=pk)
            badges.append(badge)
        except Badge.DoesNotExist:
            cart.remove(pk)
            logger.error(
                "ID {0} was in cart but doesn't exist in the database".format(pk)
            )

    order = None
    subtotal = 0
    total_discount = 0
    result = []
    orders = set()
    for badge in badges:
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

        order = badge.getOrder()
        orders.add(order)

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

    charityDonation = 0
    orgDonation = 0

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
@staff_member_required
def onsite_admin_cart(request):
    # Returns dataset to render onsite cart preview
    request.session["heartbeat"] = time.time()  # Keep session alive
    cart = request.session.get("cart", [])

    data = build_result(cart)

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

    send_mqtt_message_to_terminal(request, "payment/cart/update", terminal_data)

    return JsonResponse(data)


@require_POST
@staff_member_required
def onsite_add_to_cart(request):
    badge_ids = request.GET.getlist("id")
    assign = request.GET.get("assign") == "yes"

    try:
        badge_ids = [int(badge_id) for badge_id in badge_ids]
    except ValueError:
        return JsonResponse(
            {"success": False, "reason": "Unexpected badge ID value"}, status=400
        )

    badges = Badge.objects.filter(id__in=badge_ids)

    if len(badge_ids) > 1:
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(badge_ids)])
        badges = badges.order_by(preserved)

    if assign:
        cart = []
    else:
        cart = request.session.get("cart", [])

    for badge in badges:
        order_item = OrderItem.objects.filter(badge=badge, order__isnull=False).first()
        if order_item:
            order_items = OrderItem.objects.filter(
                order=order_item.order, badge__isnull=False
            )
            for order_item in order_items:
                if order_item.badge_id not in cart:
                    cart.append(order_item.badge_id)

    request.session["cart"] = cart

    return JsonResponse({"success": True, "cart": cart})


@require_POST
@staff_member_required
def onsite_remove_from_cart(request):
    badge_id = request.GET.get("id", None)
    try:
        badge_id = int(badge_id)
    except (TypeError, ValueError):
        return JsonResponse(
            {"success": False, "reason": "ID parameter must be integer"}, status=400
        )

    cart = request.session.get("cart", None)
    if cart is None:
        return JsonResponse({"success": False, "reason": "Cart is empty"})

    try:
        cart.remove(badge_id)
        request.session["cart"] = cart
    except ValueError:
        return JsonResponse({"success": False, "cart": cart, "reason": "Not in cart"})

    return JsonResponse({"success": True, "cart": cart})


@require_POST
@staff_member_required
def onsite_admin_clear_cart(request):
    request.session["cart"] = []
    send_mqtt_message_to_terminal(request, "payment/cart/clear")
    return JsonResponse({"success": True, "cart": []})


@require_POST
@staff_member_required
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
@staff_member_required
@permission_required("order.discount")
def create_discount(request):
    discount_type = request.POST.get("type")
    notes = request.POST.get("notes") or None
    department = None
    if department := request.POST.get("department") or None:
        department = Department.objects.get(id=int(department))

    try:
        value = Decimal(request.POST.get("value"))
    except ValueError:
        return JsonResponse({"success": False, "reason": "Unknown value provided"})

    cart = request.session.get("cart", None)
    if not cart:
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

    notes = "\n\n".join(
        item for item in [notes, f"Applied by [{request.user}]"] if item is not None
    )

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

    # Combine cart orders and apply discount to combined order
    badges = Badge.objects.filter(pk__in=cart)
    orders = [badge.getOrder() for badge in badges]
    combine_orders(orders)

    orders[0].discount = discount
    orders[0].save()

    return JsonResponse({"success": True})


@require_POST
@staff_member_required
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
@staff_member_required
def regtoken(request):
    terminal = get_active_terminal(request)
    if not terminal:
        return JsonResponse(
            {"success": False, "reason": "No terminal attached to session"}, status=400
        )

    signer = TimestampSigner()
    data = signer.sign_object(
        {
            "terminal": terminal.name,
        }
    )

    return JsonResponse({"success": True, "token": data})


@require_safe
@staff_member_required
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


@csrf_exempt
def terminal_square_token(request):
    key = request.headers.get("authorization").removeprefix("Bearer ")

    try:
        terminal = Firebase.objects.get(token=key)
    except Firebase.DoesNotExist:
        return JsonResponse(
            {"success": False, "reason": "Incorrect API key"}, status=401
        )

    base_url = "https://connect.squareup.com"
    if settings.SQUARE_ENVIRONMENT == "sandbox":
        base_url = "https://connect.squareupsandbox.com"

    scopes = ["MERCHANT_PROFILE_READ", "PAYMENTS_WRITE", "PAYMENTS_WRITE_IN_PERSON"]
    state = get_random_token(64)

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
@staff_member_required
def oauth_square(request):
    url_state = request.GET.get("state")
    cookie_state = request.COOKIES.get("square_oauth_state")

    if url_state != cookie_state:
        return JsonResponse(
            {"success": False, "reason": "Saved state did not match URL state"},
            status=400,
        )

    code = request.GET.get("code")

    token = payments.client.o_auth.obtain_token(
        client_id=settings.SQUARE_APPLICATION_ID,
        client_secret=settings.SQUARE_APPLICATION_SECRET,
        grant_type="authorization_code",
        code=code,
    )

    send_mqtt_message_to_terminal(
        request,
        "payment/update/token",
        {
            "accessToken": token.access_token,
            "refreshToken": token.refresh_token,
        },
    )

    resp = HttpResponseRedirect(reverse("registration:onsite_admin"))
    resp.delete_cookie("square_oauth_state")
    return resp


@require_POST
@staff_member_required
def print_receipts(request):
    terminal = get_active_terminal(request)
    if not terminal:
        return JsonResponse(
            {"success": False, "reason": "No terminal attached to session"}, status=400
        )

    references = request.GET.getlist("reference", [])
    orders = Order.objects.filter(reference__in=references).prefetch_related()

    for order in orders:
        if order.billingType in (Order.UNPAID, Order.COMP):
            continue

        if order.billingType == Order.CASH:
            try:
                note_data = json.loads(order.notes)
            except:
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
@staff_member_required
def fulfill(request):
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
        attendee_option.fulfilled_by = request.user
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
