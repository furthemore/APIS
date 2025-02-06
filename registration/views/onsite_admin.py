import base64
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.contrib.messages import get_messages
from django.contrib.postgres.search import TrigramSimilarity
from django.core.signing import TimestampSigner
from django.db.models import F, Func, Q, Sum, Value
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt

from registration import admin, mqtt, payments
from registration.admin import TWOPLACES
from registration.models import (
    Badge,
    Cashdrawer,
    Discount,
    Event,
    Firebase,
    Order,
    OrderItem,
)
from registration.mqtt import send_mqtt_message
from registration.pushy import PushyAPI, PushyError
from registration.views.attendee import get_attendee_age
from registration.views.common import logger
from registration.views.ordering import (
    get_discount_total,
    get_order_item_option_total,
)


def flatten(l):
    return [item for sublist in l for item in sublist]


logger = logging.getLogger(__name__)


def get_active_terminal(request):
    term_id = request.session.get("terminal")
    if term_id:
        try:
            return Firebase.objects.get(pk=int(term_id))
        except Firebase.DoesNotExist:
            return None
    return None


@staff_member_required
def onsite_admin(request):
    # Modify a dummy session variable to keep it alive
    request.session["heartbeat"] = time.time()

    terminals = list(Firebase.objects.all())
    term = request.session.get("terminal", None)

    errors = []

    # Set default payment terminal to use:
    if term is None and len(terminals) > 0:
        request.session["terminal"] = terminals[0].id

    if len(terminals) == 0:
        errors.append(
            {
                "type": "danger",
                "code": "ERROR_NO_TERMINAL",
                "text": "It looks like no payment terminals have been configured "
                "for this server yet. Check that the APIS Terminal app is "
                "running, and has been configured for the correct URL and API key.",
            }
        )

    # No terminal selection saved in session - see if one's
    # on the URL (that way it'll survive session timeouts)
    url_terminal = request.GET.get("terminal", None)
    logger.info("Terminal from GET parameter: {0}".format(url_terminal))
    if url_terminal is not None:
        try:
            terminal_obj = Firebase.objects.get(id=int(url_terminal))
            request.session["terminal"] = terminal_obj.id
        except Firebase.DoesNotExist:
            del request.session["terminal"]
            errors.append(
                {
                    "type": "warning",
                    "text": "The payment terminal specified has not registered with the server",
                }
            )
        except ValueError:
            # weren't passed an integer
            errors.append({"type": "danger", "text": "Invalid terminal specified"})

    terminal = get_active_terminal(request)
    mqtt_auth = None
    if terminal:
        mqtt_auth = mqtt.get_onsite_admin_token(terminal)

    context = {
        "settings": json.dumps({
            "debug": getattr(settings, "DEBUG", False),
            "sentry": {
                "enabled": getattr(settings, "SENTRY_ENABLED", False),
                "user_reports": getattr(settings, "SENTRY_USER_REPORTS", False),
                "frontend_dsn": getattr(settings, "SENTRY_FRONTEND_DSN", None),
                "environment": getattr(settings, "SENTRY_ENVIRONMENT", None),
                "release": getattr(settings, "SENTRY_RELEASE", None),
            },
            "errors": errors,
            "printer_uri": settings.REGISTER_PRINTER_URI,
            "mqtt": {
                "broker": getattr(settings, "MQTT_EXTERNAL_BROKER", None),
                "auth": mqtt_auth,
                "supports_printing": getattr(settings, "PRINT_VIA_MQTT", False),
            },
            "urls": {
                "assign_badge_number": reverse("registration:assign_badge_number"),
                "cash_deposit": reverse("registration:cash_deposit"),
                "cash_pickup": reverse("registration:cash_pickup"),
                "close_drawer": reverse("registration:close_drawer"),
                "close_terminal": reverse("registration:close_terminal"),
                "complete_cash_transaction": reverse("registration:complete_cash_transaction"),
                "enable_payment": reverse("registration:enable_payment"),
                "logout": reverse("registration:logout"),
                "no_sale": reverse("registration:no_sale"),
                "onsite_add_to_cart": reverse("registration:onsite_add_to_cart"),
                "onsite_admin_cart": reverse("registration:onsite_admin_cart"),
                "onsite_admin_clear_cart": reverse("registration:onsite_admin_clear_cart"),
                "onsite_admin_search": reverse("registration:onsite_admin_search"),
                "onsite_admin": reverse("registration:onsite_admin"),
                "onsite_print_badges": reverse("registration:onsite_print_badges"),
                "onsite_print_clear": reverse("registration:onsite_print_clear"),
                "onsite_remove_from_cart": reverse("registration:onsite_remove_from_cart"),
                "onsite": reverse("registration:onsite"),
                "open_drawer": reverse("registration:open_drawer"),
                "open_terminal": reverse("registration:open_terminal"),
                "pdf": reverse("registration:pdf"),
                "ready_terminal": reverse("registration:ready_terminal"),
                "registration_badge_change": reverse("admin:registration_badge_change", args=(0,)),
                "safe_drop": reverse("registration:safe_drop"),
            },
            "permissions": {
                "cash": request.user.has_perm("registration.cash"),
                "cash_admin": request.user.has_perm("registration.cash_admin"),
                "discount": request.user.has_perm("registration.discount"),
            },
            "terminals": {
                "selected": terminal.id if terminal else None,
                "available": [{"id": terminal.id, "name": terminal.name} for terminal in terminals],
            },
        }),
    }

    return render(request, "registration/onsite-admin.html", context)


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
                pass

        birthday = re.search(r"birthday:([0-9-]{10}) ?", query)
        if birthday:
            query = query.replace(birthday.group(0), "")
            birthday = birthday.group(1)

        query = query.strip()

        return SearchFields(query=query, birthday=birthday)


@staff_member_required
def onsite_admin_search(request):
    event = Event.objects.get(default=True)
    query = request.GET.get("search", None)
    if query is None:
        return redirect("registration:onsite_admin")

    data = []

    def collectBadges(badges):
        for badge in badges:
            data.append({
                "id": badge.id,
                "edit_url": reverse("admin:registration_badge_change", args=(badge.id,)),
                "attendee": {
                    "firstName": badge.attendee.firstName,
                    "lastName": badge.attendee.lastName,
                    "preferredName": badge.attendee.preferredName,
                },
                "badgeName": badge.badgeName,
                "badgeNumber": badge.badgeNumber,
                "abandoned": badge.abandoned,
            })

    query = query.strip()

    fields = SearchFields.parse(query)

    if fields.badge_ids:
        badges = Badge.objects.filter(event=event, badgeNumber__in=fields.badge_ids)
        collectBadges(badges)

    fullName = Func(F("attendee__firstName"), Value(" "), F("attendee__lastName"), function="CONCAT")
    greaterSimilarity = Func("name_similarity", "badge_similarity", function="GREATEST")

    filters = (Q(name_similarity__gte=0.4) | Q(badge_similarity__gte=0.6) | Q(attendee__lastName__iexact=fields.query))

    if fields.birthday:
        filters = filters & Q(attendee__birthdate=fields.birthday)

    results = Badge.objects.annotate(
        name_similarity=TrigramSimilarity(fullName, fields.query),
        badge_similarity=TrigramSimilarity("badgeName", fields.query),
    ).filter(
        Q(event=event) & filters
    ).order_by(greaterSimilarity).reverse().prefetch_related("attendee")[:50]

    collectBadges(results)

    return JsonResponse({"success": True, "results": data})


@staff_member_required
def close_terminal(request):
    data = {"command": "close"}
    return send_message_to_terminal(request, data)


@staff_member_required
def open_terminal(request):
    data = {"command": "open"}
    return send_message_to_terminal(request, data)


@staff_member_required
def ready_terminal(request):
    data = {"command": "ready"}
    return send_message_to_terminal(request, data)


def send_message_to_terminal(request, data):
    request.session["heartbeat"] = time.time()  # Keep session alive
    url_terminal = request.GET.get("terminal", None)
    logger.info("Terminal from GET parameter: {0}".format(url_terminal))
    session_terminal = request.session.get("terminal", None)

    if url_terminal is not None:
        try:
            active = Firebase.objects.get(id=int(url_terminal))
            request.session["terminal"] = active.id
            session_terminal = active.id
        except Firebase.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": "The payment terminal specified has not registered with the server",
                },
                status=404,
            )
        except ValueError:
            # weren't passed an integer
            return JsonResponse(
                {"success": False, "message": "Invalid terminal specified"}, status=400
            )

    try:
        active = Firebase.objects.get(id=session_terminal)
    except Firebase.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "No terminal specified and none in session"},
            status=400,
        )

    logger.info("Terminal from session: {0}".format(request.session["terminal"]))

    to = [
        active.token,
    ]

    command = data.get("command")
    if command in ("open", "close", "ready", "gay"):
        if command == "close":
            command = "closed"
        topic = f"{mqtt.get_topic('admin', active.name)}/terminal/state"
        send_mqtt_message(topic, command, True)

    try:
        PushyAPI.send_push_notification(data, to, None)
    except PushyError as e:
        return JsonResponse({"success": False, "message": e.message})
    return JsonResponse({"success": True})


@staff_member_required
def enable_payment(request):
    cart = request.session.get("cart", None)
    terminal = get_active_terminal(request)
    if cart is None:
        request.session["cart"] = []
        return JsonResponse(
            {"success": False, "message": "Cart not initialized"}, status=200
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

    data = {"command": "process_payment"}
    if terminal:
        data["terminal"] = terminal.pk
    return send_message_to_terminal(request, data)


def notify_terminal(request, data):
    # Generates preview layout based on cart items and sends the result
    # to the apropriate payment terminal for display to the customer
    term = request.session.get("terminal", None)
    if term is None:
        return
    try:
        active = Firebase.objects.get(id=term)
    except Firebase.DoesNotExist:
        return

    html = render_to_string("registration/customer-display.html", data)
    note = render_to_string("registration/customer-note.txt", data)

    logger.info(note)

    if len(data["result"]) == 0:
        display = {"command": "clear"}
    else:
        display = {
            "command": "display",
            "html": html,
            "note": note,
            "total": int(data["total"] * 100),
            "reference": data["reference"],
        }

    logger.info(display)

    # Send cloud push message
    logger.debug(note)
    to = [
        active.token,
    ]

    try:
        PushyAPI.send_push_notification(display, to, None)
    except PushyError as e:
        logger.error("Problem while sending push notification:")
        logger.error(e)
        return False
    return True


@staff_member_required
def assign_badge_number(request):
    request_badges = json.loads(request.body)

    badge_payload = {badge["id"]: badge for badge in request_badges}

    badge_set = Badge.objects.filter(id__in=list(badge_payload.keys()))

    admin.assign_badge_numbers(None, request, badge_set)
    errors = get_messages_list(request)
    if errors:
        return JsonResponse(
            {"success": False, "errors": errors, "message": "\n".join(errors)},
            status=400,
        )
    return JsonResponse({"success": True})


def get_messages_list(request):
    storage = get_messages(request)
    return [message.message for message in storage]


@staff_member_required
def onsite_print_badges(request):
    badge_list = request.GET.getlist("id")

    if getattr(settings, "PRINT_RENDERER", "wkhtmltopdf") == "gotenberg":
        terminal = get_active_terminal(request)

        signer = TimestampSigner()
        data = signer.sign_object({
            "badge_ids": [int(badge_id) for badge_id in badge_list],
            "terminal": terminal.name if terminal else None,
        })

        pdf_path = reverse("registration:pdf") + f"?data={data}"
    else:
        queryset = Badge.objects.filter(id__in=badge_list)
        pdf_name = admin.generate_badge_labels(queryset, request)

        pdf_path = reverse("registration:pdf") + f"?file={pdf_name}"

        # Async notify the frontend to refresh the cart
        logger.info("Refreshing admin cart")
        admin_push_cart_refresh(request)

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
    terminal = get_active_terminal(request)
    if terminal:
        topic = f"{mqtt.get_topic('admin', terminal.name)}/refresh"
        send_mqtt_message(topic, None)


# TODO: update for square SDK data type (fetch txn from square API and store in order.apiData)
@csrf_exempt
def complete_square_transaction(request):
    key = request.GET.get("key", "")
    reference = request.GET.get("reference")
    terminal_name = request.GET.get("terminal")
    clientTransactionId = request.GET.get("clientTransactionId")
    serverTransactionId = request.GET.get("serverTransactionId")

    if key != settings.REGISTER_KEY:
        return JsonResponse(
            {"success": False, "reason": "Incorrect API key"}, status=401
        )

    if reference is None or clientTransactionId is None:
        return JsonResponse(
            {
                "success": False,
                "reason": "Reference and clientTransactionId are required parameters",
            },
            status=400,
        )

    try:
        terminal = Firebase.objects.get(name=terminal_name)
        request.session["terminal"] = terminal.id
    except Firebase.DoesNotExist:
        request.session["terminal"] = None

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

    store_api_data = {
        "onsite": {
            "client_transaction_id": clientTransactionId,
            "server_transaction_id": serverTransactionId,
        },
    }

    order = orders[0]
    order.billingType = Order.CREDIT

    # Lookup the payment(s?) associated with this order:
    if serverTransactionId:
        for retry in range(4):
            payment_ids = payments.get_payments_from_order_id(serverTransactionId)
            if payment_ids:
                break
            time.sleep(0.5)
        if payment_ids:
            store_api_data["payment"] = {"id": payment_ids[0]}
            order.status = Order.COMPLETED
            order.settledDate = timezone.now()
            order.apiData = json.dumps(store_api_data)
        else:
            order.status = Order.CAPTURED
            order.notes = "Need to refresh payment."
    else:
        order.status = Order.CAPTURED
        order.notes = "No serverTransactionId."

    order.status = Order.COMPLETED
    order.settledDate = timezone.now()

    order.apiData = json.dumps(store_api_data)
    order.save()

    admin_push_cart_refresh(request)

    if serverTransactionId:
        status, errors = payments.refresh_payment(order, store_api_data)
        if not status:
            return JsonResponse({"success": False, "error": errors}, status=210)

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
            logger.warning("Deleting old order id={0}".format(old_order.id))
            old_order.delete()
            order_item.save()

        first_order.save()


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


@staff_member_required
@permission_required("order.cash_admin")
def no_sale(request):
    position = get_active_terminal(request)
    topic = f"{mqtt.get_topic('receipts', position.name)}/no_sale"
    send_mqtt_message(topic)

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

    topic = f"{mqtt.get_topic('receipts', position.name)}/audit_slip"

    send_mqtt_message(topic, payload)


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


@staff_member_required
@permission_required("order.cash_admin")
def open_drawer(request):
    return cash_audit_action(request, Cashdrawer.OPEN)


@staff_member_required
@permission_required("order.cash_admin")
def cash_deposit(request):
    return cash_audit_action(request, Cashdrawer.DEPOSIT)


@staff_member_required
@permission_required("order.cash_admin")
def safe_drop(request):
    return cash_audit_action(request, Cashdrawer.DROP)


@staff_member_required
@permission_required("order.cash_admin")
def cash_pickup(request):
    return cash_audit_action(request, Cashdrawer.PICKUP)


@staff_member_required
@permission_required("order.cash_admin")
def close_drawer(request):
    return cash_audit_action(request, Cashdrawer.CLOSE)


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

    term = request.session.get("terminal", None)
    active = Firebase.objects.get(id=term)
    topic = f"{mqtt.get_topic('receipts', active.name)}/print_cash"

    send_mqtt_message(topic, payload)

    return JsonResponse({"success": True})


@csrf_exempt
def firebase_register(request):
    key = request.GET.get("key", "")
    if key != settings.REGISTER_KEY:
        return JsonResponse(
            {"success": False, "reason": "Incorrect API key"}, status=401
        )

    token = request.GET.get("token", None)
    name = request.GET.get("name", None)
    if token is None or name is None:
        return JsonResponse(
            {"success": False, "reason": "Must specify token and name parameter"},
            status=400,
        )

    # Upsert if a new token with an existing name tries to register
    try:
        old_terminal = Firebase.objects.get(name=name)
        old_terminal.token = token
        old_terminal.save()
        return JsonResponse({"success": True, "updated": True})
    except Firebase.DoesNotExist:
        pass
    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "reason": "Failed while attempting to update existing name entry",
            },
            status=500,
        )

    try:
        terminal = Firebase(token=token, name=name)
        terminal.save()
    except Exception as e:
        logger.exception(e)
        logger.error("Error while saving Firebase token to database")
        return JsonResponse(
            {"success": False, "reason": "Error while saving to database"}, status=500
        )

    return JsonResponse({"success": True, "updated": False})


@csrf_exempt
def firebase_lookup(request):
    # Returns the common name stored for a given firebase token
    # (So client can notify server if either changes)
    token = request.GET.get("token", None)
    if token is None:
        return JsonResponse(
            {"success": False, "reason": "Must specify token parameter"}, status=400
        )

    try:
        terminal = Firebase.objects.get(token=token)
        return JsonResponse(
            {"success": True, "name": terminal.name, "closed": terminal.closed}
        )
    except Firebase.DoesNotExist:
        return JsonResponse(
            {"success": False, "reason": "No such token registered"}, status=404
        )


def get_discount_dict(discount):
    if discount:
        return {
            "name": discount.codeName,
            "percent_off": discount.percentOff,
            "amount_off": discount.amountOff,
            "id": discount.id,
            "valid": discount.isValid(),
            "status": discount.status,
        }
    return None


def get_line_items(attendee_options):
    out = []
    for option in attendee_options:
        if option.option.optionExtraType == "int":
            if option.optionValue:
                option_dict = {
                    "item": option.option.optionName,
                    "price": option.option.optionPrice,
                    "quantity": option.optionValue,
                    "total": option.option.optionPrice * Decimal(option.optionValue),
                }
        else:
            option_dict = {
                "item": option.option.optionName,
                "price": option.option.optionPrice,
                "quantity": 1,
                "total": option.option.optionPrice,
            }
        out.append(option_dict)
    return out


@staff_member_required
def onsite_admin_cart(request):
    # Returns dataset to render onsite cart preview
    request.session["heartbeat"] = time.time()  # Keep session alive
    cart = request.session.get("cart", [])

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
    first_order = None
    for badge in badges:
        oi = badge.getOrderItems()
        level = None
        level_subtotal = 0
        attendee_options = []
        for item in oi:
            level = item.priceLevel
            attendee_options.append(get_line_items(item.getOptions()))
            level_subtotal += get_order_item_option_total(item.getOptions())

            if level is None:
                effectiveLevel = None
            else:
                effectiveLevel = {"name": level.name, "price": level.basePrice}
                level_subtotal += level.basePrice

        subtotal += level_subtotal

        order = badge.getOrder()
        if first_order is None:
            first_order = order

        holdType = None
        if badge.attendee.holdType:
            holdType = badge.attendee.holdType.name

        level_discount = (
            Decimal(get_discount_total(order.discount, level_subtotal) * 100)
            * TWOPLACES
        )
        total_discount += level_discount

        item = {
            "id": badge.id,
            "firstName": badge.attendee.firstName,
            "lastName": badge.attendee.lastName,
            "badgeName": badge.badgeName,
            "badgeNumber": badge.badgeNumber,
            "abandoned": badge.abandoned,
            "effectiveLevel": effectiveLevel,
            "discount": get_discount_dict(order.discount),
            "age": get_attendee_age(badge.attendee),
            "holdType": holdType,
            "level_subtotal": level_subtotal,
            "level_discount": level_discount,
            "level_total": level_subtotal - level_discount,
            "attendee_options": attendee_options,
            "printed": badge.printed,
        }
        result.append(item)

    total = subtotal
    charityDonation = "?"
    orgDonation = "?"
    if order is not None:
        total += order.orgDonation + order.charityDonation
        charityDonation = order.charityDonation
        orgDonation = order.orgDonation

    data = {
        "success": True,
        "result": result,
        "subtotal": subtotal,
        "total": total - total_discount,
        "total_discount": total_discount,
        "charityDonation": charityDonation,
        "orgDonation": orgDonation,
    }

    if order is not None:
        data["order_id"] = order.id
        data["reference"] = order.reference
    else:
        data["order_id"] = None
        data["reference"] = None

    notify_terminal(request, data)

    return JsonResponse(data)


@staff_member_required
def onsite_add_to_cart(request):
    id = request.GET.get("id", None)
    return onsite_add_id_to_cart(request, id)


def onsite_add_id_to_cart(request, id):
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

    cart = request.session.get("cart", None)
    if cart is None:
        request.session["cart"] = [
            id,
        ]
        return JsonResponse({"success": True, "cart": [id]})

    if id in cart:
        return JsonResponse({"success": True, "cart": cart})

    cart.append(id)
    request.session["cart"] = cart

    return JsonResponse({"success": True, "cart": cart})


@staff_member_required
def onsite_remove_from_cart(request):
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

    cart = request.session.get("cart", None)
    if cart is None:
        return JsonResponse({"success": False, "reason": "Cart is empty"})

    try:
        cart.remove(id)
        request.session["cart"] = cart
    except ValueError:
        return JsonResponse({"success": False, "cart": cart, "reason": "Not in cart"})

    return JsonResponse({"success": True, "cart": cart})


@staff_member_required
def onsite_admin_clear_cart(request):
    request.session["cart"] = []
    send_message_to_terminal(request, {"command": "clear"})
    return JsonResponse({"success": True, "cart": []})


def get_b32_uuid():
    uid = base64.b32encode(uuid.uuid4().bytes)
    return uid[:26]


@staff_member_required
@permission_required("order.discount")
def create_discount(request):
    # e.g '$10.00' or '10%'
    amount = request.POST.get("amount")
    amount_off = Decimal("0")
    percent_off = 0

    try:
        if amount.startswith("$"):
            amount_off = Decimal(amount[1:])
        elif amount.startswith("%"):
            percent_off = int(amount[1:])
    except ValueError as e:
        return JsonResponse({"success": False, "reason": str(e)}, status=400)

    cart = request.session.get("cart", None)
    if cart is None:
        request.session["cart"] = []
        return JsonResponse(
            {"success": False, "message": "Cart not initialized"}, status=400
        )

    discount = Discount(
        codeName=get_b32_uuid(),
        percentOff=percent_off,
        amountOff=amount_off,
        startDate=timezone.now(),
        endDate=timezone.now() + datetime.timedelta(hours=1),
        notes=f"Applied by [{request.user}]",
        oneTime=True,
        used=1,
        reason="Onsite admin discount",
    )
    discount.save()

    # Combine cart orders and apply discount to combined order
    badges = Badge.objects.filter(pk__in=cart)
    orders = [badge.getOrder() for badge in badges]
    combine_orders(orders)

    orders[0].discount = discount
    orders[0].save()

    JsonResponse({"success": True, "order": orders[0].pk})


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
