import json
import logging

from django.forms import model_to_dict
from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render

import registration.emails
from registration.models import *

from . import common
from .common import (
    clear_session,
    get_client_ip,
    get_registration_email,
    getOptionsDict,
    handler,
    logger,
)
from .ordering import do_checkout, doZeroCheckout, get_total

logger = logging.getLogger(__name__)


def upgrade(request, guid):
    event = Event.objects.get(default=True)
    context = {"token": guid, "event": event}
    return render(request, "registration/attendee-locate.html", context)


def info_upgrade(request):
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for info_upgrade()")
        return JsonResponse({"success": False}, status=400)

    email = postData.get("email")
    token = postData.get("token")
    if email is None or token is None:
        return HttpResponseBadRequest("email, token are required fields")

    badge = get_object_or_404(Badge, registrationToken=token)

    attendee = badge.attendee
    if attendee.email.lower() != email.lower():
        return HttpResponseNotFound("No Record Found")

    request.session["attendee_id"] = attendee.id
    request.session["badge_id"] = badge.id
    return JsonResponse({"success": True, "message": "ATTENDEE"})


def find_upgrade(request):
    event = Event.objects.get(default=True)
    context = {"attendee": None, "event": event}
    try:
        attendee_id = request.session["attendee_id"]
        badge_id = request.session["badge_id"]
    except KeyError:
        return render(
            request, "registration/attendee-upgrade.html", context, status=400
        )

    attendee = get_object_or_404(Attendee, id=attendee_id)
    badge = get_object_or_404(Badge, id=badge_id)
    attendee_dict = model_to_dict(attendee)
    badge_dict = {"id": badge.id}
    level = badge.effectiveLevel()
    existing_order_items = badge.getOrderItems()
    level_dict = {
        "basePrice": level.basePrice,
        "options": getOptionsDict(existing_order_items),
    }
    context = {
        "attendee": attendee,
        "badge": badge,
        "event": event,
        "jsonAttendee": json.dumps(attendee_dict, default=handler),
        "jsonBadge": json.dumps(badge_dict, default=handler),
        "jsonLevel": json.dumps(level_dict, default=handler),
    }
    return render(request, "registration/attendee-upgrade.html", context)


def add_upgrade(request):
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for add_upgrade()")
        return JsonResponse({"success": False})

    pda = postData["attendee"]
    pdp = postData["priceLevel"]
    pdd = postData["badge"]
    evt = postData["event"]
    event = Event.objects.get(name=evt)

    if "attendee_id" not in request.session:
        return HttpResponseServerError("Session expired")

    # Update Attendee info
    attendee = Attendee.objects.get(id=pda["id"])
    if not attendee:
        return HttpResponseServerError("Attendee id not found")

    badge = Badge.objects.get(id=pdd["id"])
    priceLevel = PriceLevel.objects.get(id=int(pdp["id"]))

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    for option in pdp["options"]:
        plOption = PriceLevelOption.objects.get(id=int(option["id"]))
        attendeeOption = AttendeeOptions(
            option=plOption, orderItem=orderItem, optionValue=option["value"]
        )
        attendeeOption.save()

    orderItems = request.session.get("order_items", [])
    orderItems.append(orderItem.id)
    request.session["order_items"] = orderItems

    return JsonResponse({"success": True})


def invoice_upgrade(request):
    sessionItems = request.session.get("order_items", [])
    if not sessionItems:
        context = {"orderItems": [], "total": 0, "discount": {}}
        clear_session(request)
    else:
        attendeeId = request.session.get("attendee_id", -1)
        badgeId = request.session.get("badge_id", -1)
        if attendeeId == -1 or badgeId == -1:
            context = {"orderItems": [], "total": 0, "discount": {}}
            clear_session(request)
        else:
            badge = Badge.objects.get(id=badgeId)
            attendee = Attendee.objects.get(id=attendeeId)
            lvl = badge.effectiveLevel()
            lvl_dict = {"basePrice": lvl.basePrice}
            orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
            total, total_discount = get_total([], orderItems)
            context = {
                "orderItems": orderItems,
                "total": total,
                "total_discount": total_discount,
                "attendee": attendee,
                "prevLevel": lvl_dict,
                "event": badge.event,
            }
    return render(request, "registration/upgrade-checkout.html", context)


def done_upgrade(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/upgrade-done.html", context)


def send_upgrade_email(request, attendee, order):
    event = Event.objects.get(default=True)
    clear_session(request)
    try:
        registration.emails.send_upgrade_payment_email(attendee, order)
    except Exception as e:
        logger.exception("Error sending UpgradePaymentEmail")
        registration_email = get_registration_email(event)
        return JsonResponse(
            {
                "success": False,
                "message": "Your upgrade payment succeeded but we may have been unable to send you a "
                "confirmation email. If you do not receive one within the next hour, please "
                "contact {0} to get your confirmation number.".format(
                    registration_email
                ),
            }
        )
    return JsonResponse({"success": True})


def checkout_upgrade(request):
    session_items = request.session.get("order_items", [])
    order_items = list(OrderItem.objects.filter(id__in=session_items))
    if "attendee_id" not in request.session:
        return HttpResponseBadRequest("Session expired")

    attendee = Attendee.objects.get(id=request.session.get("attendee_id"))
    try:
        post_data = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for checkout_upgrade()")
        return common.abort(400, "Unable to parse input options")

    subtotal, total_discount = get_total([], order_items)

    if subtotal == 0:
        status, message, order = doZeroCheckout(None, None, order_items)

        if not status:
            return common.abort(400, message)

        return send_upgrade_email(request, attendee, order)

    porg = Decimal(post_data.get("orgDonation") or "0.00")
    pcharity = Decimal(post_data.get("charityDonation") or "0.00")
    if porg < 0:
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity

    pbill = post_data["billingData"]
    status, message, order = do_checkout(
        pbill, total, None, [], order_items, porg, pcharity
    )

    if status:
        return send_upgrade_email(request, attendee, order)
    else:
        order.delete()
        return common.abort(400, message)
