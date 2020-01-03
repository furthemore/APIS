import logging
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from registration.models import *

logger = logging.getLogger("django.request")


def flush(request):
    request.session.flush()
    return JsonResponse({"success": True})


def in_group(groupname):
    def inner(user):
        return user.groups.filter(name=groupname).exists()

    return inner


def clear_session(request):
    """
    Soft-clears session by removing any non-protected session values.
    (anything prefixed with '_'; keeps Django user logged-in)
    """
    for key in request.session.keys():
        if key[0] != "_":
            del request.session[key]


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_request_meta(request):
    values = {}
    values["HTTP_REFERER"] = request.META.get("HTTP_REFERER")
    values["HTTP_USER_AGENT"] = request.META.get("HTTP_USER_AGENT")
    values["IP"] = get_client_ip(request)
    return json.dumps(values)


def getOptionsDict(orderItems):
    orderDict = []
    for oi in orderItems:
        aos = oi.getOptions()
        for ao in aos:
            if (
                ao.optionValue == 0
                or ao.optionValue is None
                or ao.optionValue == ""
                or ao.optionValue == False
            ):
                pass
            try:
                orderDict.append(
                    {
                        "name": ao.option.optionName,
                        "value": ao.optionValue,
                        "id": ao.option.id,
                        "image": ao.option.optionImage.url,
                    }
                )
            except BaseException:
                orderDict.append(
                    {
                        "name": ao.option.optionName,
                        "value": ao.optionValue,
                        "id": ao.option.id,
                        "image": None,
                    }
                )

            orderDict.append(
                {
                    "name": ao.option.optionName,
                    "value": ao.optionValue,
                    "id": ao.option.id,
                    "type": ao.option.optionExtraType,
                }
            )
    return orderDict


def getEvents(request):
    events = Event.objects.all()
    data = [
        {
            "name": ev.name,
            "id": ev.id,
            "dealerStart": ev.dealerRegStart,
            "dealerEnd": ev.dealerRegEnd,
            "staffStart": ev.staffRegStart,
            "staffEnd": ev.staffRegEnd,
            "attendeeStart": ev.attendeeRegStart,
            "attendeeEnd": ev.attendeeRegEnd,
        }
        for ev in events
    ]
    return HttpResponse(
        json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )


def abort(status=400, reason="Bad request"):
    """
    Returns a JSON response indicating an error to the client.

    status: A valid HTTP status code
    reason: Human-readable explanation
    """
    logger.error("JSON {0}: {1}".format(status, reason))
    return JsonResponse({"success": False, "reason": reason}, status=status)


def success(status=200, reason=None):
    """
    Returns a JSON response indicating success.

    status: A valid HTTP status code (2xx)
    reason: (Optional) human-readable explanation
    """
    if reason is None:
        logger.debug("JSON {0}".format(status))
        return JsonResponse({"success": True}, status=status)
    else:
        logger.debug("JSON {0}: {1}".format(status, reason))
        return JsonResponse(
            {
                "success": True,
                "reason": reason,
                "message": reason,  # Backwards compatibility
            },
            status=status,
        )


def getConfirmationToken():
    return "".join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(6)
    )


def handler(obj):
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return str(obj)
    else:
        raise TypeError(
            "Object of type %s with value of %s is not JSON serializable"
            % (type(obj), repr(obj),)
        )


def index(request):
    try:
        event = Event.objects.get(default=True)
    except Event.DoesNotExist:
        return render(request, "registration/docs/no-event.html")

    tz = timezone.get_current_timezone()
    today = tz.localize(datetime.now())
    context = {"event": event}
    if event.attendeeRegStart <= today <= event.attendeeRegEnd:
        return render(request, "registration/registration-form.html", context)
    return render(request, "registration/closed.html", context)


@staff_member_required
@user_passes_test(in_group("Manager"))
def manualDiscount(request):
    # FIXME stub
    raise NotImplementedError


@staff_member_required
def basicBadges(request):
    badges = Badge.objects.all()
    staff = Staff.objects.all()
    event = Event.objects.get(default=True)

    bdata = [
        {
            "badgeName": badge.badgeName,
            "level": badge.effectiveLevel().name,
            "assoc": badge.abandoned,
            "firstName": badge.attendee.firstName.lower(),
            "lastName": badge.attendee.lastName.lower(),
            "printed": badge.printed,
            "discount": badge.getDiscount(),
            "orderItems": getOptionsDict(badge.orderitem_set.all()),
        }
        for badge in badges
        if badge.effectiveLevel() is not None and badge.event == event
    ]

    staffdata = [
        {
            "firstName": s.attendee.firstName.lower(),
            "lastName": s.attendee.lastName.lower(),
            "title": s.title,
            "id": s.id,
        }
        for s in staff
        if s.event == event
    ]

    for staff in staffdata:
        sbadge = Staff.objects.get(id=staff["id"]).getBadge()
        if sbadge:
            staff["badgeName"] = sbadge.badgeName
            if sbadge.effectiveLevel():
                staff["level"] = sbadge.effectiveLevel().name
            else:
                staff["level"] = "none"
            staff["assoc"] = sbadge.abandoned
            staff["orderItems"] = getOptionsDict(sbadge.orderitem_set.all())

    sdata = sorted(bdata, key=lambda x: (x["level"], x["lastName"]))
    ssdata = sorted(staffdata, key=lambda x: x["lastName"])

    dealers = [att for att in sdata if att["assoc"] == "Dealer"]
    staff = [att for att in ssdata]
    attendees = [att for att in sdata if att["assoc"] != "Staff"]
    return render(
        request,
        "registration/utility/badgelist.html",
        {"attendees": attendees, "dealers": dealers, "staff": staff},
    )


@staff_member_required
def vipBadges(request):
    badges = Badge.objects.all()
    # Assumes VIP levels based on being marked as "vip" group, or EmailVIP set
    priceLevels = PriceLevel.objects.filter(Q(emailVIP=True) | Q(group__iexact="vip"))
    vipLevels = [level.name for level in priceLevels]

    # FIXME list comprehension is sloooooooow - there must be a way to do this in SQL -R
    bdata = [
        {
            "badge": badge,
            "orderItems": getOptionsDict(badge.orderitem_set.all()),
            "level": badge.effectiveLevel().name,
            "assoc": badge.abandoned,
        }
        for badge in badges
        if badge.effectiveLevel() is not None
        and badge.effectiveLevel() != "Unpaid"
        and badge.effectiveLevel().name in vipLevels
        and badge.abandoned != "Staff"
    ]

    events = Event.objects.all()
    # FIXME this doesn't actually affect the order in the resulting template render
    events.reverse()

    return render(
        request,
        "registration/utility/holidaylist.html",
        {"badges": bdata, "events": events},
    )


def getDepartments(request):
    depts = Department.objects.filter(volunteerListOk=True).order_by("name")
    data = [{"name": item.name, "id": item.id} for item in depts]
    return HttpResponse(json.dumps(data), content_type="application/json")


def getAllDepartments(request):
    depts = Department.objects.order_by("name")
    data = [{"name": item.name, "id": item.id} for item in depts]
    return HttpResponse(json.dumps(data), content_type="application/json")


def getShirtSizes(request):
    sizes = ShirtSizes.objects.all()
    data = [{"name": size.name, "id": size.id} for size in sizes]
    return HttpResponse(json.dumps(data), content_type="application/json")


def getSessionAddresses(request):
    event = Event.objects.get(default=True)
    sessionItems = request.session.get("cart_items", [])
    if not sessionItems:
        # might be from dealer workflow, which is order items in the session
        sessionItems = request.session.get("order_items", [])
        if not sessionItems:
            data = {}
        else:
            orderItems = OrderItem.objects.filter(id__in=sessionItems)
            data = [
                {
                    "id": oi.badge.attendee.id,
                    "fname": oi.badge.attendee.firstName,
                    "lname": oi.badge.attendee.lastName,
                    "email": oi.badge.attendee.email,
                    "address1": oi.badge.attendee.address1,
                    "address2": oi.badge.attendee.address2,
                    "city": oi.badge.attendee.city,
                    "state": oi.badge.attendee.state,
                    "country": oi.badge.attendee.country,
                    "postalCode": oi.badge.attendee.postalCode,
                }
                for oi in orderItems
            ]
    else:
        data = []
        cartItems = list(Cart.objects.filter(id__in=sessionItems))
        for cart in cartItems:
            cartJson = json.loads(cart.formData)
            pda = cartJson["attendee"]
            cartItem = {
                "fname": pda["firstName"],
                "lname": pda["lastName"],
                "email": pda["email"],
                "phone": pda["phone"],
            }
            if event.collectAddress:
                cartItem.update(
                    {
                        "address1": pda["address1"],
                        "address2": pda["address2"],
                        "city": pda["city"],
                        "state": pda["state"],
                        "postalCode": pda["postal"],
                        "country": pda["country"],
                    }
                )

            data.append(cartItem)
    return HttpResponse(json.dumps(data), content_type="application/json")


def getRegistrationEmail(event=None):
    """
    Retrieves the email address to show on error messages in the attendee
    registration form for a specified event.  If no event specified, uses
    the first default event.  If no email is listed there, returns the
    default of APIS_DEFAULT_EMAIL in settings.py.
    """
    if event is None:
        try:
            event = Event.objects.get(default=True)
        except BaseException:
            return settings.APIS_DEFAULT_EMAIL
    if event.registrationEmail == "":
        return settings.APIS_DEFAULT_EMAIL
    return event.registrationEmail
