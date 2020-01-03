from django.forms import model_to_dict
from django.http import HttpResponseServerError, JsonResponse
from django.shortcuts import render

import registration.emails
from registration.models import *
from registration.views.common import (
    get_client_ip,
    getOptionsDict,
    getRegistrationEmail,
    handler,
    logger,
)
from registration.views.orders import doCheckout, doZeroCheckout, getTotal


def upgrade(request, guid):
    event = Event.objects.get(default=True)
    context = {"token": guid, "event": event}
    return render(request, "registration/attendee-locate.html", context)


def infoUpgrade(request):
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for infoUpgrade()")
        return JsonResponse({"success": False})

    try:
        email = postData["email"]
        token = postData["token"]

        evt = postData["event"]
        event = Event.objects.get(name=evt)

        badge = Badge.objects.get(registrationToken=token)
        if not badge:
            return HttpResponseServerError("No Record Found")

        attendee = badge.attendee
        if attendee.email.lower() != email.lower():
            return HttpResponseServerError("No Record Found")

        request.session["attendee_id"] = attendee.id
        request.session["badge_id"] = badge.id
        return JsonResponse({"success": True, "message": "ATTENDEE"})
    except Exception as e:
        logger.exception("Error in starting upgrade.")
        return HttpResponseServerError(str(e))


def findUpgrade(request):
    event = Event.objects.get(default=True)
    context = {"attendee": None, "event": event}
    try:
        attId = request.session["attendee_id"]
        badgeId = request.session["badge_id"]
    except Exception as e:
        return render(request, "registration/attendee-upgrade.html", context)

    attendee = Attendee.objects.get(id=attId)
    if attendee:
        badge = Badge.objects.get(id=badgeId)
        attendee_dict = model_to_dict(attendee)
        badge_dict = {"id": badge.id}
        lvl = badge.effectiveLevel()
        existingOIs = badge.getOrderItems()
        lvl_dict = {"basePrice": lvl.basePrice, "options": getOptionsDict(existingOIs)}
        context = {
            "attendee": attendee,
            "badge": badge,
            "event": event,
            "jsonAttendee": json.dumps(attendee_dict, default=handler),
            "jsonBadge": json.dumps(badge_dict, default=handler),
            "jsonLevel": json.dumps(lvl_dict, default=handler),
        }
    return render(request, "registration/attendee-upgrade.html", context)


def addUpgrade(request):
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for addUpgrade()")
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


def invoiceUpgrade(request):
    sessionItems = request.session.get("order_items", [])
    if not sessionItems:
        context = {"orderItems": [], "total": 0, "discount": {}}
        request.session.flush()
    else:
        attendeeId = request.session.get("attendee_id", -1)
        badgeId = request.session.get("badge_id", -1)
        if attendeeId == -1 or badgeId == -1:
            context = {"orderItems": [], "total": 0, "discount": {}}
            request.session.flush()
        else:
            badge = Badge.objects.get(id=badgeId)
            attendee = Attendee.objects.get(id=attendeeId)
            lvl = badge.effectiveLevel()
            lvl_dict = {"basePrice": lvl.basePrice}
            orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
            total, total_discount = getTotal([], orderItems)
            context = {
                "orderItems": orderItems,
                "total": total,
                "total_discount": total_discount,
                "grand_total": total - lvl_dict["basePrice"],
                "attendee": attendee,
                "prevLevel": lvl_dict,
                "event": badge.event,
            }
    return render(request, "registration/upgrade-checkout.html", context)


def doneUpgrade(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/upgrade-done.html", context)


def checkoutUpgrade(request):
    try:
        sessionItems = request.session.get("order_items", [])
        orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
        if "attendee_id" not in request.session:
            return HttpResponseServerError("Session expired")

        attendee = Attendee.objects.get(id=request.session.get("attendee_id"))
        try:
            postData = json.loads(request.body)
        except ValueError as e:
            logger.error("Unable to decode JSON for checkoutUpgrade()")
            return JsonResponse({"success": False})

        event = Event.objects.get(default=True)

        subtotal, total_discount = getTotal([], orderItems)

        if subtotal == 0:
            status, message, order = doZeroCheckout(None, None, orderItems)

            if not status:
                return JsonResponse({"success": False, "message": message})

            request.session.flush()
            try:
                registration.emails.sendUpgradePaymentEmail(attendee, order)
            except Exception as e:
                logger.exception("Error sending UpgradePaymentEmail - zero sum.")
                registrationEmail = getRegistrationEmail(event)
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Your upgrade payment succeeded but we may have been unable to send you a confirmation email. If you do not receive one within the next hour, please contact {0} to get your confirmation number.".format(
                            registrationEmail
                        ),
                    }
                )
            return JsonResponse({"success": True})

        porg = Decimal(postData["orgDonation"].strip() or "0.00")
        pcharity = Decimal(postData["charityDonation"].strip() or "0.00")
        if porg < 0:
            porg = 0
        if pcharity < 0:
            pcharity = 0

        total = subtotal + porg + pcharity

        pbill = postData["billingData"]
        ip = get_client_ip(request)
        status, message, order = doCheckout(
            pbill, total, None, [], orderItems, porg, pcharity
        )

        if status:
            request.session.flush()
            try:
                registration.emails.sendUpgradePaymentEmail(attendee, order)
            except Exception as e:
                logger.exception("Error sending UpgradePaymentEmail.")
                registrationEmail = getRegistrationEmail(event)
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Your upgrade payment succeeded but we may have been unable to send you a confirmation email. If you do not receive one within the next hour, please contact {0} to get your confirmation number.".format(
                            registrationEmail
                        ),
                    }
                )
            return JsonResponse({"success": True})
        else:
            order.delete()
            return JsonResponse({"success": False, "message": message})

    except Exception as e:
        logger.exception("Error in attendee upgrade.")
        return HttpResponseServerError(str(e))
