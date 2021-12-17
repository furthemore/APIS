import json
import logging
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.db.models.fields.files import FieldFile
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render

import registration.emails
from registration.models import *
from registration.payments import charge_payment
from registration.views.cart import saveCart

logger = logging.getLogger("django.request")


def flush(request):
    clear_session(request)
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
    for key in list(request.session.keys()):
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

    return orderDict


def get_events(request):
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
    elif isinstance(obj, FieldFile):
        try:
            return obj.url
        except ValueError:
            return None
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
    discount = request.session.get("discount")
    if discount:
        discount = Discount.objects.filter(codeName=discount)
        if discount.count() > 0:
            discount = discount.first()

    context = {"event": event, "discount": discount}
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
    event = Event.objects.get(default=True)

    staff = Staff.objects.filter(event=event)
    order_items = OrderItem.objects.filter(badge__event=event)

    bdata = [
        {
            "badgeName": oi.badge.badgeName,
            "level": oi.badge.effectiveLevel(),
            "assoc": oi.badge.abandoned,
            "firstName": oi.badge.attendee.firstName.lower(),
            "lastName": oi.badge.attendee.lastName.lower(),
            "printed": oi.badge.printed,
            "discount": oi.badge.getDiscount(),
            "orderItems": getOptionsDict(oi.badge.orderitem_set.all()),
        }
        for oi in order_items
    ]

    staffdata = [
        {
            "firstName": s.attendee.firstName.lower(),
            "lastName": s.attendee.lastName.lower(),
            "title": s.title,
            "id": s.id,
        }
        for s in staff
    ]

    for staff in staffdata:
        sbadge = Staff.objects.get(id=staff["id"]).getBadge()
        if sbadge:
            staff["badgeName"] = sbadge.badgeName
            if sbadge.effectiveLevel():
                staff["level"] = sbadge.effectiveLevel()
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
    default_event = Event.objects.get(default=True)
    event_id = request.GET.get("event", default_event.id)
    event = get_object_or_404(Event, id=event_id)

    # Assumes VIP levels based on being marked as "vip" group, or EmailVIP set
    price_levels = PriceLevel.objects.filter(Q(emailVIP=True) | Q(group__iexact="vip"))

    vip_order_items = OrderItem.objects.filter(
        priceLevel__in=price_levels, badge__event=event
    )

    badges = [
        {
            "badge": oi.badge,
            "orderItems": getOptionsDict(oi.badge.orderitem_set.all()),
            "level": oi.badge.effectiveLevel(),
            "assoc": oi.badge.abandoned,
        }
        for oi in vip_order_items
        if oi.badge.abandoned != "Staff"
    ]

    return render(
        request,
        "registration/utility/holidaylist.html",
        {"badges": badges, "event": event},
    )


def get_departments(request):
    depts = Department.objects.filter(volunteerListOk=True).order_by("name")
    data = [{"name": item.name, "id": item.id} for item in depts]
    return HttpResponse(json.dumps(data), content_type="application/json")


def get_all_departments(request):
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


def doCheckout(
    billingData, total, discount, cartItems, orderItems, donationOrg, donationCharity,
):
    event = Event.objects.get(default=True)
    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).exists():
        reference = getConfirmationToken()

    order = Order(
        total=Decimal(total),
        reference=reference,
        discount=discount,
        orgDonation=donationOrg,
        charityDonation=donationCharity,
    )

    # Address collection is marked as required by event
    if event.collectBillingAddress:
        try:
            order.billingName = "{0} {1}".format(
                billingData["cc_firstname"], billingData["cc_lastname"]
            )
            order.billingAddress1 = billingData["address1"]
            order.billingAddress2 = billingData["address2"]
            order.billingCity = billingData["city"]
            order.billingState = billingData["state"]
            order.billingCountry = billingData["country"]
            order.billingEmail = billingData["email"]
        except KeyError as e:
            abort(
                400,
                "Address collection is required, but request is missing required field: {0}".format(
                    e
                ),
            )

    # Otherwise, no need for anything except postal code (Square US/CAN)
    try:
        card_data = billingData["card_data"]
        order.billingPostal = card_data["billing_postal_code"]
        order.lastFour = card_data["last_4"]
    except KeyError as e:
        abort(400, "A required field was missing from billingData: {0}".format(e))

    status, response = charge_payment(order, billingData)

    if status:
        if cartItems:
            for item in cartItems:
                orderItem = saveCart(item)
                orderItem.order = order
                orderItem.save()
        elif orderItems:
            for oitem in orderItems:
                oitem.order = order
                oitem.save()
        order.status = "Paid"
        order.save()
        if discount:
            discount.used = discount.used + 1
            discount.save()
        return True, "", order

    return False, response, order


def doZeroCheckout(discount, cartItems, orderItems):
    if cartItems:
        attendee = json.loads(cartItems[0].formData)["attendee"]
        billingName = "{firstName} {lastName}".format(**attendee)
        billingEmail = attendee["email"]
    elif orderItems:
        attendee = orderItems[0].badge.attendee
        billingName = "{0} {1}".format(attendee.firstName, attendee.lastName)
        billingEmail = attendee.email

    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    logger.debug(attendee)
    order = Order(
        total=0,
        reference=reference,
        discount=discount,
        orgDonation=0,
        charityDonation=0,
        status="Complete",
        billingType=Order.COMP,
        billingEmail=billingEmail,
        billingName=billingName,
    )
    order.save()

    if cartItems:
        for item in cartItems:
            orderItem = saveCart(item)
            orderItem.order = order
            orderItem.save()
    elif orderItems:
        for oitem in orderItems:
            oitem.order = order
            oitem.save()

    if discount:
        discount.used = discount.used + 1
        discount.save()

    return True, "", order


def getCartItemOptionTotal(options):
    optionTotal = 0
    for option in options:
        optionData = PriceLevelOption.objects.get(id=option["id"])
        if optionData.optionExtraType == "int":
            if option["value"]:
                optionTotal += optionData.optionPrice * Decimal(option["value"])
        else:
            optionTotal += optionData.optionPrice
    return optionTotal


def getOrderItemOptionTotal(options):
    optionTotal = 0
    for option in options:
        if option.option.optionExtraType == "int":
            if option.optionValue:
                optionTotal += option.option.optionPrice * Decimal(option.optionValue)
        else:
            optionTotal += option.option.optionPrice
    return optionTotal


def getDiscountTotal(disc, subtotal):
    discount = Discount.objects.get(codeName=disc)
    if discount.isValid():
        if discount.amountOff:
            return discount.amountOff
        elif discount.percentOff:
            return Decimal(float(subtotal) * float(discount.percentOff) / 100)


def getTotal(cartItems, orderItems, disc=""):
    total = 0
    total_discount = 0
    if not cartItems and not orderItems:
        return 0, 0
    for item in cartItems:
        postData = json.loads(item.formData)
        pdp = postData["priceLevel"]
        priceLevel = PriceLevel.objects.get(id=pdp["id"])
        itemTotal = priceLevel.basePrice

        options = pdp["options"]
        itemTotal += getCartItemOptionTotal(options)

        if disc:
            discount = getDiscountTotal(disc, itemTotal)
            total_discount += discount
            itemTotal -= discount

        if itemTotal > 0:
            total += itemTotal

    for item in orderItems:
        itemSubTotal = item.priceLevel.basePrice
        effLevel = item.badge.effectiveLevel()

        if effLevel:
            itemTotal = itemSubTotal - effLevel.basePrice
        else:
            itemTotal = itemSubTotal

        itemTotal += getOrderItemOptionTotal(item.attendeeoptions_set.all())

        if disc:
            discount = getDiscountTotal(disc, itemTotal)
            total_discount += discount
            itemTotal -= discount

        # FIXME Why?
        if itemTotal > 0:
            total += itemTotal

    return total, total_discount


def applyDiscount(request):
    dis = request.session.get("discount", "")
    if dis:
        return JsonResponse(
            {"success": False, "message": "Only one discount is allowed per order."}
        )

    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for apply_discount()")
        return JsonResponse({"success": False})
    dis = postData["discount"]

    discount = Discount.objects.filter(codeName=dis)
    if discount.count() == 0:
        return JsonResponse(
            {"success": False, "message": "That discount is not valid."}
        )
    discount = discount.first()
    if not discount.isValid():
        return JsonResponse(
            {"success": False, "message": "That discount is not valid."}
        )

    request.session["discount"] = discount.codeName
    return JsonResponse({"success": True})


def checkout(request):
    event = Event.objects.get(default=True)
    sessionItems = request.session.get("cart_items", [])
    cartItems = list(Cart.objects.filter(id__in=sessionItems))
    orderItems = request.session.get("order_items", [])
    pdisc = request.session.get("discount", "")

    # Safety valve (in case session times out before checkout is complete)
    if len(sessionItems) == 0 and len(orderItems) == 0:
        abort(400, "Session expired or no session is stored for this client")

    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.error("Unable to decode JSON for checkout()")
        return abort(400, "Unable to parse input options")

    discount = Discount.objects.filter(codeName=pdisc)
    if discount.count() > 0 and discount.first().isValid():
        discount = discount.first()
    else:
        discount = None

    if orderItems:
        orderItems = list(OrderItem.objects.filter(id__in=orderItems))

    subtotal, _ = getTotal(cartItems, orderItems, discount)

    if subtotal == 0:
        status, message, order = doZeroCheckout(discount, cartItems, orderItems)
        if not status:
            return abort(400, message)

        # Attach attendee to dealer assistant:
        add_attendee_to_assistant(request, order.badge.attendee)
        clear_session(request)
        try:
            registration.emails.send_registration_email(order, order.billingEmail)
        except Exception as e:
            logger.error("Error sending RegistrationEmail - zero sum.")
            logger.exception(e)
            registrationEmail = getRegistrationEmail(event)
            return abort(
                400,
                "Your payment succeeded but we may have been unable to send you a confirmation email. If you do not receive one within the next hour, please contact {0} to get your confirmation number.".format(
                    registrationEmail
                ),
            )
        return success()

    porg = Decimal(postData["orgDonation"].strip() or "0.00")
    pcharity = Decimal(postData["charityDonation"].strip() or "0.00")
    pbill = postData["billingData"]

    if porg < 0:
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity
    ip = get_client_ip(request)

    onsite = postData["onsite"]
    if onsite:
        reference = getConfirmationToken()
        order = Order(
            total=Decimal(total),
            reference=reference,
            discount=discount,
            orgDonation=porg,
            charityDonation=pcharity,
            billingType=Order.UNPAID,
        )
        order.status = "Onsite Pending"
        order.save()

        if cartItems:
            for item in cartItems:
                orderItem = saveCart(item)
                orderItem.order = order
                orderItem.save()
        while Order.objects.filter(reference=reference).count() > 0:
            reference = getConfirmationToken()

        if discount:
            discount.used = discount.used + 1
            discount.save()

        status = True
        message = "Onsite success"
    else:
        status, message, order = doCheckout(
            pbill, total, discount, cartItems, orderItems, porg, pcharity
        )

    if status:
        add_attendee_to_assistant(request, order.badge.attendee)
        # Delete cart when done
        cartItems = Cart.objects.filter(id__in=sessionItems)
        cartItems.delete()
        clear_session(request)
        try:
            registration.emails.send_registration_email(order, order.billingEmail)
        except Exception as e:
            event = Event.objects.get(default=True)
            registrationEmail = getRegistrationEmail(event)

            logger.error("Error sending RegistrationEmail.")
            logger.exception(e)
            return abort(
                500,
                "Your payment succeeded but we may have been unable to send you a confirmation email. If you do not receive one within the next hour, please contact {0} to get your confirmation number.".format(
                    registrationEmail
                ),
            )
        return success()
    else:
        return abort(400, message)


def deleteOrderItem(id):
    orderItems = OrderItem.objects.filter(id=id)
    if orderItems.count() == 0:
        return
    orderItem = orderItems.first()
    orderItem.badge.attendee.delete()
    orderItem.badge.delete()
    orderItem.delete()
