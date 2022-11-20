import json
import logging
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.forms import model_to_dict
from django.http import (
    Http404,
    HttpResponseNotFound,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import render
from django.views.decorators.http import require_POST

import registration.emails
from registration.models import *

from .common import (
    abort,
    clear_session,
    get_client_ip,
    handler,
    logger,
    success,
)
from .ordering import doCheckout, doZeroCheckout, getTotal

logger = logging.getLogger(__name__)


def new_staff(request, guid):
    event = Event.objects.get(default=True)
    context = {"token": guid, "event": event}
    return render(request, "registration/staff/staff-new.html", context)


@require_POST
def find_new_staff(request):
    try:
        post_data = json.loads(request.body)
        email = post_data["email"]
        token = post_data["token"]

        token = TempToken.objects.get(email__iexact=email, token=token)

        if token.validUntil < timezone.now():
            return abort(400, "Invalid Token")
        if token.used:
            return abort(400, "Token Used")

        request.session["new_staff"] = token.token

        return JsonResponse({"success": True, "message": "STAFF"})
    except ObjectDoesNotExist:
        return abort(404, "No staff found")
    except json.JSONDecodeError as e:
        return abort(400, e.msg)


def info_new_staff(request):
    event = Event.objects.get(default=True)
    token_value = request.session.get("new_staff")
    context = {"staff": None, "event": event}
    try:
        context["token"] = TempToken.objects.get(token=token_value)
    except ObjectDoesNotExist:
        return render(
            request, "registration/staff/staff-new-payment.html", context, status=404
        )
    return render(request, "registration/staff/staff-new-payment.html", context)


@require_POST
def add_new_staff(request):
    postData = json.loads(request.body)
    # create attendee from request post
    pda = postData["attendee"]
    pds = postData["staff"]
    pdp = postData["priceLevel"]
    evt = postData.get("event")

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


def staff_index(request, guid):
    event = Event.objects.get(default=True)
    context = {"token": guid, "event": event}
    return render(request, "registration/staff/staff-locate.html", context)


def staff_done(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/staff/staff-done.html", context)


@require_POST
def find_staff(request):
    try:
        post_data = json.loads(request.body)
        email = post_data["email"]
        token = post_data["token"]
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Unable to find staff: bad request - {request.body}")
        return abort(400, str(e))

    try:
        staff = Staff.objects.get(
            attendee__email__iexact=email, registrationToken=token
        )
    except ObjectDoesNotExist:
        return abort(404, "Staff matching query does not exist.")

    request.session["staff_id"] = staff.id
    return JsonResponse({"success": True, "message": "STAFF"})


def info_staff(request):
    event = Event.objects.get(default=True)
    context = {"staff": None, "event": event}

    staff_id = request.session.get("staff_id")
    if staff_id is None:
        return render(request, "registration/staff/staff-payment.html", context)

    staff = Staff.objects.get(id=staff_id)
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


def add_staff(request):
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for add_staff()")
        return JsonResponse({"success": False})

    # create attendee from request post
    pda = postData["attendee"]
    pds = postData["staff"]
    pdp = postData["priceLevel"]
    evt = postData.get("event")

    if evt:
        event = Event.objects.get(name=evt)
    else:
        event = Event.objects.get(default=True)

    attendee = Attendee.objects.get(id=pda["id"])
    if not attendee:
        return JsonResponse({"success": False, "message": "Attendee not found"})

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda["birthdate"], "%Y-%m-%d"))

    attendee.preferredName = pda.get("preferredName", "")
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


def get_staff_total(orderItems, discount, staff):
    badge = Badge.objects.get(attendee=staff.attendee, event=staff.event)

    if badge.effectiveLevel():
        discount = None
    subTotal = getTotal(orderItems, discount)
    alreadyPaid = badge.paidTotal()
    total = subTotal - alreadyPaid

    if total < 0:
        return 0
    return total


def get_staff_email(event=None):
    """
    Retrieves the email address to show on error messages in the staff
    registration form for a specified event.  If no event specified, uses
    the first default event.  If no email is listed there, returns the
    default of APIS_DEFAULT_EMAIL in settings.py.
    """
    if event is None:
        event = Event.objects.get(default=True)
    if event.staffEmail == "":
        return settings.APIS_DEFAULT_EMAIL
    return event.staffEmail


def checkout_staff(request):
    session_items = request.session.get("order_items", [])
    pdisc = request.session.get("discount", "")
    staff_id = request.session["staff_id"]
    order_items = list(OrderItem.objects.filter(id__in=session_items))
    try:
        post_data = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for checkout_staff()")
        return abort(400, str(e))

    event = Event.objects.get(default=True)
    discount = event.staffDiscount
    staff = Staff.objects.get(id=staff_id)
    subtotal = get_staff_total(order_items, discount, staff)

    if subtotal == 0:
        status, message, order = doZeroCheckout(discount, None, order_items)
        if not status:
            return abort(400, status)

        clear_session(request)
        try:
            registration.emails.send_staff_registration_email(order.id)
        except Exception as e:
            logger.error("Error emailing StaffRegistrationEmail - zero sum.")
            staff_email = get_staff_email()
            return abort(
                400,
                f"Your registration succeeded but we may have been unable to send you a confirmation "
                f"email. If you have any questions, please contact {staff_email} to get your confirmation "
                f"number.",
            )
        return JsonResponse({"success": True})

    pbill = post_data["billingData"]
    porg = Decimal(post_data["orgDonation"].strip() or "0.00")
    pcharity = Decimal(post_data["charityDonation"].strip() or "0.00")
    if porg < 0:
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity
    ip = get_client_ip(request)

    status, message, order = doCheckout(
        pbill, total, discount, order_items, porg, pcharity, ip
    )

    if status:
        clear_session(request)
        try:
            registration.emails.send_staff_registration_email(order.id)
        except Exception as e:
            logger.exception("Error emailing StaffRegistrationEmail.")
            staff_email = get_staff_email()
            return abort(
                400,
                f"Your registration succeeded but we may have been unable to send you a confirmation email. If you "
                f"have any questions, please contact {staff_email} to get your confirmation number.",
            )
        return success()
    else:
        order.delete()
        return abort(400, message)
