import json
import logging
from datetime import datetime
from time import timezone

from django.core.exceptions import ObjectDoesNotExist
from django.forms import model_to_dict
from django.http import JsonResponse
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
from .ordering import do_checkout, doZeroCheckout, get_total

logger = logging.getLogger(__name__)
form_type = "staff"


def new_staff(request, guid):
    event = Event.objects.get(default=True)
    invite = TempToken.objects.get(token=guid)
    tz = timezone.get_current_timezone()
    today = tz.localize(datetime.now())
    context = {"token": guid, "event": event, "form_type": form_type}
    if event.staffRegStart <= today <= event.staffRegEnd or invite.ignore_time_window is True:
        return render(request, "registration/staff/staff-new.html", context)
    elif event.staffRegStart >= today:
        context["message"] = "is not yet open. Please stay tuned to slack and email for updates!"
        return render(request, "registration/staff/staff-closed.html", context)
    elif event.staffRegEnd <= today:
        context["message"] = "has ended."
        return render(request, "registration/staff/staff-closed.html", context)


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
    context = {"staff": None, "event": event, "form_type": form_type}
    try:
        context["token"] = TempToken.objects.get(token=token_value)
    except ObjectDoesNotExist:
        return render(
            request, "registration/staff/staff-new-payment.html", context, status=404
        )
    return render(request, "registration/staff/staff-new-payment.html", context)


def staff_from_post_data(pds, attendee, event, staff):
    shirt = ShirtSizes.objects.get(id=pds["shirtsize"])
    if not staff:
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
    return staff


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

    staff_from_post_data(pds, attendee, event, None)

    price_level = PriceLevel.objects.get(id=int(pdp["id"]))

    order_item = OrderItem(badge=badge, priceLevel=price_level, enteredBy="WEB")
    order_item.save()

    for option in pdp["options"]:
        pl_option = PriceLevelOption.objects.get(id=int(option["id"]))
        attendee_option = AttendeeOptions(
            option=pl_option, orderItem=order_item, optionValue=option["value"]
        )
        attendee_option.save()

    order_items = request.session.get("order_items", [])
    order_items.append(order_item.id)
    request.session["order_items"] = order_items

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
    tz = timezone.get_current_timezone()
    today = tz.localize(datetime.now())
    context = {"token": guid, "event": event, "form_type": form_type}
    if event.staffRegStart <= today <= event.staffRegEnd:
        return render(request, "registration/staff/staff-locate.html", context)
    elif event.staffRegStart >= today:
        context["message"] = "is not yet open. Please stay tuned to slack and email for updates!"
        return render(request, "registration/staff/staff-closed.html", context)
    elif event.staffRegEnd <= today:
        context["message"] = "has ended."
        return render(request, "registration/staff/staff-closed.html", context)


def staff_done(request):
    event = Event.objects.get(default=True)
    context = {"event": event, "form_type": form_type}
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
    context = {"staff": None, "event": event, "form_type": form_type}

    staff_id = request.session.get("staff_id")
    if staff_id is None:
        return render(request, "registration/staff/staff-payment.html", context)

    staff = Staff.objects.get(id=staff_id)
    if staff:
        staff_dict = model_to_dict(staff)
        attendee_dict = model_to_dict(staff.attendee)
        badges = Badge.objects.filter(attendee=staff.attendee, event=staff.event)

        badge = {}
        paid_total = 0
        if badges.count() > 0:
            badge = badges[0]
            paid_total = badge.paidTotal()

        context = {
            "staff": staff,
            "jsonStaff": json.dumps(staff_dict, default=handler),
            "jsonAttendee": json.dumps(attendee_dict, default=handler),
            "badge": badge,
            "event": event,
            "paid_total": paid_total,
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

    staff_from_post_data(pds, attendee, event, staff)

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

    price_level = PriceLevel.objects.get(id=int(pdp["id"]))

    order_item = OrderItem(badge=badge, priceLevel=price_level, enteredBy="WEB")
    order_item.save()

    for option in pdp["options"]:
        pl_option = PriceLevelOption.objects.get(id=int(option["id"]))
        attendee_option = AttendeeOptions(
            option=pl_option, orderItem=order_item, optionValue=option["value"]
        )
        attendee_option.save()

    order_items = request.session.get("order_items", [])
    order_items.append(order_item.id)
    request.session["order_items"] = order_items

    discount = event.staffDiscount
    if discount:
        request.session["discount"] = discount.codeName

    staff.resetToken()

    return JsonResponse({"success": True})


def get_staff_total(orderItems, discount, staff):
    badge = Badge.objects.get(attendee=staff.attendee, event=staff.event)

    if badge.effectiveLevel():
        discount = None
    sub_total = get_total(orderItems, discount)
    already_paid = badge.paidTotal()
    total = sub_total - already_paid

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
