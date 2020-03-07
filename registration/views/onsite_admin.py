import json
import logging
import subprocess
import time
from datetime import datetime

from attendee import get_attendee_age
from common import logger
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from printing import printNametag

from registration import admin, payments, printing
from registration.admin import TWOPLACES
from registration.models import *
from registration.pushy import PushyAPI, PushyError
from registration.views.ordering import getDiscountTotal, getOrderItemOptionTotal

flatten = lambda l: [item for sublist in l for item in sublist]
logger = logging.getLogger(__name__)


def send_mqtt_message(topic, payload):
    payload_json = json.dumps(payload, cls=JSONDecimalEncoder)

    mqtt_command = [
        "mosquitto_pub",
        "-h",
        settings.MQTT_BROKER["host"],
        "-p",
        str(settings.MQTT_BROKER["port"]),
        "-t",
        topic,
        "-u",
        settings.MQTT_LOGIN["username"],
        "-P",
        settings.MQTT_LOGIN["password"],
        "-m",
        payload_json,
    ]
    logger.info("Sending MQTT message ({0})".format(payload_json))
    try:
        subprocess.check_call(mqtt_command)
    except subprocess.CalledProcessError as exc:
        logger.info("Failed to send MQTT message: {0!s}".format(exc))
    else:
        logger.info("Sent MQTT message successfully.")


@staff_member_required
def onsiteAdmin(request):
    # Modify a dummy session variable to keep it alive
    request.session["heartbeat"] = time.time()

    event = Event.objects.get(default=True)
    terminals = list(Firebase.objects.all())
    term = request.session.get("terminal", None)
    query = request.GET.get("search", None)

    errors = []
    results = None

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
            errors.append(
                {
                    "type": "warning",
                    "text": "The payment terminal specified has not registered with the server",
                }
            )
        except ValueError:
            # weren't passed an integer
            errors.append({"type": "danger", "text": "Invalid terminal specified"})

    if query is not None:
        results = Badge.objects.filter(
            Q(attendee__lastName__icontains=query)
            | Q(attendee__firstName__icontains=query),
            Q(event=event),
        )
        if len(results) == 0:
            errors.append(
                {"type": "warning", "text": 'No results for query "{0}"'.format(query)}
            )

    context = {
        "terminals": terminals,
        "errors": errors,
        "results": results,
        "printer_uri": settings.REGISTER_PRINTER_URI,
    }

    return render(request, "registration/onsite-admin.html", context)


@staff_member_required
def onsiteAdminSearch(request):
    event = Event.objects.get(default=True)
    terminals = list(Firebase.objects.all())
    query = request.POST.get("search", None)
    if query is None:
        return redirect("registration:onsiteAdmin")

    errors = []
    results = Badge.objects.filter(
        Q(attendee__lastName__icontains=query)
        | Q(attendee__firstName__icontains=query),
        Q(event=event),
    )
    if len(results) == 0:
        errors = [
            {"type": "warning", "text": 'No results for query "{0}"'.format(query)}
        ]

    context = {"terminals": terminals, "errors": errors, "results": results}
    return render(request, "registration/onsite-admin.html", context)


@staff_member_required
def closeTerminal(request):
    data = {"command": "close"}
    return sendMessageToTerminal(request, data)


@staff_member_required
def openTerminal(request):
    data = {"command": "open"}
    return sendMessageToTerminal(request, data)


def sendMessageToTerminal(request, data):
    # import pdb; pdb.set_trace()
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

    try:
        PushyAPI.sendPushNotification(data, to, None)
    except PushyError as e:
        return JsonResponse({"success": False, "message": e.message})
    return JsonResponse({"success": True})


@staff_member_required
def enablePayment(request):
    cart = request.session.get("cart", None)
    if cart is None:
        request.session["cart"] = []
        return JsonResponse(
            {"success": False, "message": "Cart not initialized"}, status=200
        )

    badges = []
    first_order = None

    for id in cart:
        try:
            badge = Badge.objects.get(id=id)
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
            cart.remove(id)
            logger.error(
                "ID {0} was in cart but doesn't exist in the database".format(id)
            )

    # Force a cart refresh to get the latest order reference to the terminal
    onsiteAdminCart(request)

    data = {"command": "process_payment"}
    return sendMessageToTerminal(request, data)


def notifyTerminal(request, data):
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
        PushyAPI.sendPushNotification(display, to, None)
    except PushyError as e:
        logger.error("Problem while sending push notification:")
        logger.error(e)
        return False
    return True


def assignBadgeNumber(request):
    event = Event.objects.get(default=True)

    request_badges = json.loads(request.body)

    badge_payload = {badge["id"]: badge for badge in request_badges}

    badge_list = [b["id"] for b in request_badges]
    badge_set = Badge.objects.filter(id__in=badge_payload.keys())

    reserved_badges = ReservedBadgeNumbers.objects.filter(event=event)
    reserved_badge_numbers = [badge.badgeNumber for badge in reserved_badges]

    errors = []

    for badge in badge_set.order_by("registeredDate"):
        # Skip badges which have already been assigned
        # if badge.badgeNumber is not None:
        #    errors.append(
        #        "{0} was already assigned badge number {1}.".format(
        #            badge, badge.badgeNumber
        #        )
        #    )
        #    continue
        # Skip badges that are not assigned a registration level
        if badge.effectiveLevel() is None:
            errors.append("{0} is not assigned a registration level.".format(badge))
            continue

        # Check if proposed badge number is reserved:
        if badge_payload[badge.id]["badgeNumber"] in reserved_badge_numbers:
            errors.append(
                "{0} is a reserved badge number. {1} was not assigned a badge number.".format(
                    badge.request_badges["badgeNumber"], badge
                )
            )
            continue

        badge.badgeNumber = badge_payload[badge.id]["badgeNumber"]
        badge.save()

    if errors:
        return JsonResponse(
            {"success": False, "errors": errors, "message": "\n".join(errors)},
            status=400,
        )
    return JsonResponse({"success": True})


@staff_member_required
def onsitePrintBadges(request):
    badge_list = request.GET.getlist("id")
    con = printing.Main(local=True)
    tags = []
    theme = ""

    for badge_id in badge_list:
        try:
            badge = Badge.objects.get(id=badge_id)
        except Badge.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Badge id {0} does not exist".format(badge_id),
                },
                status=404,
            )

        theme = badge.event.badgeTheme

        if badge.badgeNumber is None:
            badgeNumber = ""
        else:
            badgeNumber = "{:04}".format(badge.badgeNumber)

        tags.append(
            {
                "name": badge.badgeName,
                "number": badgeNumber,
                "level": str(badge.effectiveLevel()),
                "title": "",
                "age": get_attendee_age(badge.attendee),
            }
        )
        badge.printed = True
        badge.save()

    if theme == "":
        theme == "apis"
    con.nametags(tags, theme=theme)
    pdf_path = con.pdf.split("/")[-1]

    file_url = reverse("registration:print") + "?file={0}".format(pdf_path)

    return JsonResponse(
        {
            "success": True,
            "file": pdf_path,
            "next": request.get_full_path(),
            "url": file_url,
        }
    )


def onsiteSignature(request):
    context = {}
    return render(request, "registration/signature.html", context)


# TODO: update for square SDK data type (fetch txn from square API and store in order.apiData)
@csrf_exempt
def completeSquareTransaction(request):
    key = request.GET.get("key", "")
    # FIXME: Need to work on a list of order references, so that every order gets
    # FIXME: updated and no badge is left orphaned.
    reference = request.GET.get("reference", None)
    clientTransactionId = request.GET.get("clientTransactionId", None)
    serverTransactionId = request.GET.get("serverTransactionId", None)

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

    # Things we need:
    #   orderID or reference (passed to square by metadata)
    # Square returns:
    #   clientTransactionId (offline payments)
    #   serverTransactionId (online payments)

    try:
        # order = Order.objects.get(reference=reference)
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

    # If there is more than one order, we should flatten them into one by reassigning all these
    # orderItems to the first order, and deleting the rest.
    first_order = orders[0]
    if len(orders) > 1:

        order_items = []
        for order in orders[1:]:
            order_items += order.orderitem_set.all()

        for order_item in order_items:
            old_order = order_item.order
            order_item.order = first_order
            logger.warn("Deleting old order id={0}".format(old_order.id))
            old_order.delete()
            order_item.save()

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
            order.settledDate = datetime.now()
            order.notes = json.dumps(store_api_data)
        else:
            order.status = Order.CAPTURED
            order.notes = "Need to refresh payment."
    else:
        order.status = Order.CAPTURED
        order.notes = "No serverTransactionId."

    order.apiData = json.dumps(store_api_data)
    order.save()

    status, errors = payments.refresh_payment(order, store_api_data)

    if not status:
        return JsonResponse({"success": False, "error": errors,}, status=210)

    return JsonResponse({"success": True})


class JSONDecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o.quantize(Decimal("1.00")))
        return o


# json.dumps(the_thing, cls=JSONDecimalEncoder)


def completeCashTransaction(request):
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
        order = Order.objects.get(reference=reference)
    except Order.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "reason": "No order matching the reference specified exists",
            },
            status=404,
        )

    order.billingType = Order.CASH
    order.status = Order.COMPLETED
    order.settledDate = datetime.now()
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
        "donations": {"org": {"name": event.name, "price": str(order.orgDonation)},},
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
    topic = "apis/receipts/{0}/print_cash".format(active.name)

    send_mqtt_message(topic, payload)

    return JsonResponse({"success": True})


@csrf_exempt
def firebaseRegister(request):
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
def firebaseLookup(request):
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
def onsiteAdminCart(request):
    # Returns dataset to render onsite cart preview
    request.session["heartbeat"] = time.time()  # Keep session alive
    cart = request.session.get("cart", None)
    if cart is None:
        request.session["cart"] = []
        return JsonResponse(
            {"success": False, "message": "Cart not initialized"}, status=200
        )

    badges = []
    for id in cart:
        try:
            badge = Badge.objects.get(id=id)
            badges.append(badge)
        except Badge.DoesNotExist:
            cart.remove(id)
            logger.error(
                "ID {0} was in cart but doesn't exist in the database".format(id)
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
            attendee_options.append(get_line_items(item.attendeeoptions_set.all()))
            level_subtotal += getOrderItemOptionTotal(item.attendeeoptions_set.all())

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
            Decimal(getDiscountTotal(order.discount, level_subtotal) * 100) * TWOPLACES
        )
        total_discount += level_discount

        item = {
            "id": badge.id,
            "firstName": badge.attendee.firstName,
            "lastName": badge.attendee.lastName,
            "badgeName": badge.badgeName,
            "abandoned": badge.abandoned,
            "effectiveLevel": effectiveLevel,
            "discount": get_discount_dict(order.discount),
            "age": get_attendee_age(badge.attendee),
            "holdType": holdType,
            "level_subtotal": level_subtotal,
            "level_discount": level_discount,
            "level_total": level_subtotal - level_discount,
            "attendee_options": attendee_options,
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

    notifyTerminal(request, data)

    return JsonResponse(data)


@staff_member_required()
def onsiteSignaturePrompt(request):
    data = {
        "command": "signature",
        "name": "Kasper Finch",
        "agreement": "I have read and agree to the FurTheMore 2020 Code of Conduct",
        "badge_id": "5",
    }
    return sendMessageToTerminal(request, data)


@staff_member_required
def onsiteAddToCart(request):
    id = request.GET.get("id", None)
    if id is None or id == "":
        return JsonResponse(
            {"success": False, "reason": "Need ID parameter"}, status=400
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
def onsiteRemoveFromCart(request):
    id = request.GET.get("id", None)
    if id is None or id == "":
        return JsonResponse(
            {"success": False, "reason": "Need ID parameter"}, status=400
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
def onsiteAdminClearCart(request):
    request.session["cart"] = []
    sendMessageToTerminal(request, {"command": "clear"})
    return onsiteAdmin(request)
