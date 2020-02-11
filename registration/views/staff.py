import json
from datetime import datetime

from common import abort, clear_session, get_client_ip, handler, logger, success
from django.forms import model_to_dict
from django.http import HttpResponseServerError, JsonResponse
from django.shortcuts import render
from ordering import doCheckout, doZeroCheckout, getTotal

from registration import emails
from registration.models import *


def newStaff(request, guid):
    event = Event.objects.get(default=True)
    context = {"token": guid, "event": event}
    return render(request, "registration/staff/staff-new.html", context)


def findNewStaff(request):
    try:
        postData = json.loads(request.body)
        email = postData["email"]
        token = postData["token"]

        token = TempToken.objects.get(email__iexact=email, token=token)
        if not token:
            return HttpResponseServerError("No Staff Found")

        if token.validUntil < timezone.now():
            return HttpResponseServerError("Invalid Token")
        if token.used:
            return HttpResponseServerError("Token Used")

        request.session["newStaff"] = token.token

        return JsonResponse({"success": True, "message": "STAFF"})
    except Exception as e:
        logger.exception("Unable to find staff." + request.body)
        return HttpResponseServerError(str(e))


def infoNewStaff(request):
    event = Event.objects.get(default=True)
    try:
        tokenValue = request.session["newStaff"]
        token = TempToken.objects.get(token=tokenValue)
    except Exception as e:
        token = None
    context = {"staff": None, "event": event, "token": token}
    return render(request, "registration/staff/staff-new-payment.html", context)


def addNewStaff(request):
    postData = json.loads(request.body)
    # create attendee from request post
    pda = postData["attendee"]
    pds = postData["staff"]
    pdp = postData["priceLevel"]
    evt = postData["event"]

    if evt:
        event = Event.objects.get(name=evt)
    else:
        event = Event.objects.get(default=True)

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda["birthdate"], "%Y-%m-%d"))

    attendee = Attendee(
        firstName=pda["firstName"],
        lastName=pda["lastName"],
        address1=pda["address1"],
        address2=pda["address2"],
        city=pda["city"],
        state=pda["state"],
        country=pda["country"],
        postalCode=pda["postal"],
        phone=pda["phone"],
        email=pda["email"],
        birthdate=birthdate,
        emailsOk=True,
        surveyOk=False,
    )
    attendee.save()

    badge = Badge(attendee=attendee, event=event, badgeName=pda["badgeName"])
    badge.save()

    shirt = ShirtSizes.objects.get(id=pds["shirtsize"])

    staff = Staff(attendee=attendee, event=event)
    staff.twitter = pds["twitter"]
    staff.telegram = pds["telegram"]
    staff.shirtsize = shirt
    staff.specialSkills = pds["specialSkills"]
    staff.specialFood = pds["specialFood"]
    staff.specialMedical = pds["specialMedical"]
    staff.contactName = pds["contactName"]
    staff.contactPhone = pds["contactPhone"]
    staff.contactRelation = pds["contactRelation"]
    staff.save()

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

    discount = event.newStaffDiscount
    if discount:
        request.session["discount"] = discount.codeName

    tokens = TempToken.objects.filter(email=attendee.email)
    for token in tokens:
        token.used = True
        token.save()

    return JsonResponse({"success": True})


def staff(request, guid):
    event = Event.objects.get(default=True)
    context = {"token": guid, "event": event}
    return render(request, "registration/staff/staff-locate.html", context)


def staffDone(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/staff/staff-done.html", context)


def findStaff(request):
    try:
        postData = json.loads(request.body)
        email = postData["email"]
        token = postData["token"]

        staff = Staff.objects.get(
            attendee__email__iexact=email, registrationToken=token
        )
        if not staff:
            return HttpResponseServerError("No Staff Found")

        request.session["staff_id"] = staff.id
        return JsonResponse({"success": True, "message": "STAFF"})
    except Exception as e:
        logger.warning("Unable to find staff. " + request.body)
        return HttpResponseServerError(str(e))


def infoStaff(request):
    event = Event.objects.get(default=True)
    context = {"staff": None, "event": event}
    try:
        staffId = request.session["staff_id"]
    except Exception as e:
        return render(request, "registration/staff/staff-payment.html", context)

    staff = Staff.objects.get(id=staffId)
    if staff:
        staff_dict = model_to_dict(staff)
        attendee_dict = model_to_dict(staff.attendee)
        badges = Badge.objects.filter(attendee=staff.attendee, event=staff.event)

        badge = {}
        if badges.count() > 0:
            badge = badges[0]

        context = {
            "staff": staff,
            "jsonStaff": json.dumps(staff_dict, default=handler),
            "jsonAttendee": json.dumps(attendee_dict, default=handler),
            "badge": badge,
            "event": event,
        }
    return render(request, "registration/staff/staff-payment.html", context)


def addStaff(request):
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for addStaff()")
        return JsonResponse({"success": False})

    event = Event.objects.get(default=True)

    # create attendee from request post
    pda = postData["attendee"]
    pds = postData["staff"]
    pdp = postData["priceLevel"]
    evt = postData["event"]

    if evt:
        event = Event.objects.get(name=evt)
    else:
        event = Event.objects.get(default=True)

    attendee = Attendee.objects.get(id=pda["id"])
    if not attendee:
        return JsonResponse({"success": False, "message": "Attendee not found"})

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda["birthdate"], "%Y-%m-%d"))

    attendee.firstName = pda["firstName"]
    attendee.lastName = pda["lastName"]
    attendee.address1 = pda["address1"]
    attendee.address2 = pda["address2"]
    attendee.city = pda["city"]
    attendee.state = pda["state"]
    attendee.country = pda["country"]
    attendee.postalCode = pda["postal"]
    attendee.birthdate = birthdate
    attendee.phone = pda["phone"]
    attendee.emailsOk = True
    attendee.surveyOk = False  # staff get their own survey

    try:
        attendee.save()
    except Exception as e:
        logger.exception("Error saving staff attendee record.")
        return JsonResponse({"success": False, "message": "Attendee not saved: " + e})

    staff = Staff.objects.get(id=pds["id"])
    if "staff_id" not in request.session:
        return JsonResponse({"success": False, "message": "Staff record not found"})

    # Update Staff info
    if not staff:
        return JsonResponse({"success": False, "message": "Staff record not found"})

    shirt = ShirtSizes.objects.get(id=pds["shirtsize"])
    staff.twitter = pds["twitter"]
    staff.telegram = pds["telegram"]
    staff.shirtsize = shirt
    staff.specialSkills = pds["specialSkills"]
    staff.specialFood = pds["specialFood"]
    staff.specialMedical = pds["specialMedical"]
    staff.contactName = pds["contactName"]
    staff.contactPhone = pds["contactPhone"]
    staff.contactRelation = pds["contactRelation"]

    try:
        staff.save()
    except Exception as e:
        logger.exception("Error saving staff record.")
        return JsonResponse({"success": False, "message": "Staff not saved: " + str(e)})

    badges = Badge.objects.filter(attendee=attendee, event=event)
    if badges.count() == 0:
        badge = Badge(attendee=attendee, event=event, badgeName=pda["badgeName"])
    else:
        badge = badges[0]
        badge.badgeName = pda["badgeName"]

    try:
        badge.save()
    except Exception as e:
        logger.exception("Error saving staff badge record.")
        return JsonResponse({"success": False, "message": "Badge not saved: " + str(e)})

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

    discount = event.staffDiscount
    if discount:
        request.session["discount"] = discount.codeName

    staff.resetToken()

    return JsonResponse({"success": True})


def getStaffTotal(orderItems, discount, staff):
    badge = Badge.objects.get(attendee=staff.attendee, event=staff.event)

    if badge.effectiveLevel():
        discount = None
    subTotal = getTotal(orderItems, discount)
    alreadyPaid = badge.paidTotal()
    total = subTotal - alreadyPaid

    if total < 0:
        return 0
    return total


def checkoutStaff(request):
    sessionItems = request.session.get("order_items", [])
    pdisc = request.session.get("discount", "")
    staffId = request.session["staff_id"]
    orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for checkoutStaff()")
        return JsonResponse({"success": False})

    event = Event.objects.get(default=True)
    discount = event.staffDiscount
    staff = Staff.objects.get(id=staffId)
    subtotal = getStaffTotal(orderItems, discount, staff)

    if subtotal == 0:
        status, message, order = doZeroCheckout(discount, None, orderItems)
        if not status:
            return JsonResponse({"success": False, "message": message})

        clear_session(request)
        try:
            emails.sendStaffRegistrationEmail(order.id)
        except Exception as e:
            logger.exception("Error emailing StaffRegistrationEmail - zero sum.")
            staffEmail = getStaffEmail()
            return JsonResponse(
                {
                    "success": False,
                    "message": "Your registration succeeded but we may have been unable to send you a confirmation email. If you have any questions, please contact {0} to get your confirmation number.".format(
                        staffEmail
                    ),
                }
            )
        return JsonResponse({"success": True})

    pbill = postData["billingData"]
    porg = Decimal(postData["orgDonation"].strip() or "0.00")
    pcharity = Decimal(postData["charityDonation"].strip() or "0.00")
    if porg < 0:
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity
    ip = get_client_ip(request)

    status, message, order = doCheckout(
        pbill, total, discount, orderItems, porg, pcharity, ip
    )

    if status:
        clear_session(request)
        try:
            emails.sendStaffRegistrationEmail(order.id)
        except Exception as e:
            logger.exception("Error emailing StaffRegistrationEmail.")
            staffEmail = getStaffEmail()
            return abort(
                400,
                "Your registration succeeded but we may have been unable to send you a confirmation email. If you have any questions, please contact {0} to get your confirmation number.".format(
                    staffEmail
                ),
            )
        return success()
    else:
        order.delete()
        return abort(400, message)


def getStaffEmail(event=None):
    """
    Retrieves the email address to show on error messages in the staff
    registration form for a specified event.  If no event specified, uses
    the first default event.  If no email is listed there, returns the
    default of APIS_DEFAULT_EMAIL in settings.py.
    """
    if event is None:
        try:
            event = Event.objects.get(default=True)
        except BaseException:
            return settings.APIS_DEFAULT_EMAIL
    if event.staffEmail == "":
        return settings.APIS_DEFAULT_EMAIL
    return event.staffEmail
