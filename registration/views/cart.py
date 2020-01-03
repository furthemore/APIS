import logging
from datetime import datetime

from django.shortcuts import render

from registration.models import *
from registration.views.attendee import checkBanList
from registration.views.common import (
    abort,
    get_request_meta,
    getRegistrationEmail,
    logger,
    success,
)
from registration.views.orders import *


def getCart(request):
    sessionItems = request.session.get("cart_items", [])
    sessionOrderItems = request.session.get("order_items", [])
    discount = request.session.get("discount", "")
    event = None
    if not sessionItems and not sessionOrderItems:
        context = {"orderItems": [], "total": 0, "discount": {}}
        request.session.flush()
    elif sessionOrderItems:
        orderItems = list(OrderItem.objects.filter(id__in=sessionOrderItems))
        if discount:
            discount = Discount.objects.filter(codeName=discount)
            if discount.count() > 0:
                discount = discount.first()
        total, total_discount = getTotal([], orderItems, discount)

        hasMinors = False
        for item in orderItems:
            if item.badge.isMinor():
                hasMinors = True
                break

        event = Event.objects.get(default=True)
        context = {
            "event": event,
            "orderItems": orderItems,
            "total": total,
            "total_discount": total_discount,
            "discount": discount,
            "hasMinors": hasMinors,
        }

    elif sessionItems:
        cartItems = list(Cart.objects.filter(id__in=sessionItems))
        orderItems = []
        if discount:
            discount = Discount.objects.filter(codeName=discount)
            if discount.count() > 0:
                discount = discount.first()
        total, total_discount = getTotal(cartItems, [], discount)

        hasMinors = False
        for cart in cartItems:
            cartJson = json.loads(cart.formData)
            pda = cartJson["attendee"]
            event = Event.objects.get(name=cartJson["event"])
            evt = event.eventStart
            tz = timezone.get_current_timezone()
            birthdate = tz.localize(datetime.strptime(pda["birthdate"], "%Y-%m-%d"))
            age_at_event = (
                evt.year
                - birthdate.year
                - ((evt.month, evt.day) < (birthdate.month, birthdate.day))
            )
            if age_at_event < 18:
                hasMinors = True

            pdp = cartJson["priceLevel"]
            priceLevel = PriceLevel.objects.get(id=pdp["id"])
            pdo = pdp["options"]
            options = []
            for option in pdo:
                dataOption = {}
                optionData = PriceLevelOption.objects.get(id=option["id"])
                if optionData.optionExtraType == "int":
                    if option["value"]:
                        itemTotal = optionData.optionPrice * Decimal(option["value"])
                        dataOption = {
                            "name": optionData.optionName,
                            "number": option["value"],
                            "total": itemTotal,
                        }
                else:
                    itemTotal = optionData.optionPrice
                    dataOption = {"name": optionData.optionName, "total": itemTotal}
                options.append(dataOption)
            orderItem = {
                "id": cart.id,
                "attendee": pda,
                "priceLevel": priceLevel,
                "options": options,
            }
            orderItems.append(orderItem)

        if event is None:
            event = Event.objects.get(default=True)
        context = {
            "event": event,
            "orderItems": orderItems,
            "total": total,
            "total_discount": total_discount,
            "discount": discount,
            "hasMinors": hasMinors,
        }
    return render(request, "registration/checkout.html", context)


def saveCart(cart):
    postData = json.loads(cart.formData)
    pda = postData["attendee"]
    pdp = postData["priceLevel"]
    evt = postData["event"]

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda["birthdate"], "%Y-%m-%d"))

    event = Event.objects.get(name=evt)

    attendee = Attendee(
        firstName=pda["firstName"],
        lastName=pda["lastName"],
        phone=pda["phone"],
        email=pda["email"],
        birthdate=birthdate,
        emailsOk=bool(pda["emailsOk"]),
        volunteerContact=len(pda["volDepts"]) > 0,
        volunteerDepts=pda["volDepts"],
        surveyOk=bool(pda["surveyOk"]),
        aslRequest=bool(pda["asl"]),
    )

    if event.collectAddress:
        try:
            attendee.address1 = pda["address1"]
            attendee.address2 = pda["address2"]
            attendee.city = pda["city"]
            attendee.state = pda["state"]
            attendee.country = pda["country"]
            attendee.postalCode = pda["postal"]
        except KeyError:
            logging.error(
                "Supposed to be collecting addresses, but wasn't provided by form!"
            )
    attendee.save()

    badge = Badge(badgeName=pda["badgeName"], event=event, attendee=attendee)
    badge.save()

    priceLevel = PriceLevel.objects.get(id=int(pdp["id"]))

    via = "WEB"
    if postData["attendee"].get("onsite", False):
        via = "ONSITE"

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy=via)
    orderItem.save()

    for option in pdp["options"]:
        plOption = PriceLevelOption.objects.get(id=int(option["id"]))
        if plOption.optionExtraType == "int" and option["value"] == "":
            attendeeOption = AttendeeOptions(
                option=plOption, orderItem=orderItem, optionValue="0"
            )
        else:
            if option["value"] != "":
                attendeeOption = AttendeeOptions(
                    option=plOption, orderItem=orderItem, optionValue=option["value"]
                )
        attendeeOption.save()

    cart.transferedDate = datetime.now()
    cart.save()

    return orderItem


def addToCart(request):
    """
    Create attendee from request post.
    """
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        return abort(400, "Unable to decode JSON body")

    event = Event.objects.get(default=True)

    try:
        pda = postData["attendee"]
        pda["firstName"]
        pda["lastName"]
        pda["email"]
    except KeyError:
        return abort(400, "Required parameters not found in POST body")

    banCheck = checkBanList(pda["firstName"], pda["lastName"], pda["email"])
    if banCheck:
        logger.error("***ban list registration attempt***")
        registrationEmail = getRegistrationEmail()
        return abort(
            403,
            "We are sorry, but you are unable to register for {0}. If you have any questions, or would like further information or assistance, please contact Registration at {1}".format(
                event, registrationEmail
            ),
        )

    cart = Cart(
        form=Cart.ATTENDEE, formData=request.body, formHeaders=get_request_meta(request)
    )
    cart.save()

    # add attendee to session order
    cartItems = request.session.get("cart_items", [])
    cartItems.append(cart.id)
    request.session["cart_items"] = cartItems
    return success()


def removeFromCart(request):
    # locate attendee in session order
    deleted = False
    order = request.session.get("order_items", [])
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        return abort(400, "Unable to decode JSON parameters")
    if "id" not in postData.keys():
        return abort(400, "Required parameter `id` not specified")
    id = postData["id"]

    # Old workflow
    logger.debug("order_items: {0}".format(order))
    logger.debug("delete order from session: {0}".format(id))
    if int(id) in order:
        order.remove(int(id))
        deleted = True
        request.session["order_items"] = order
        return success()

    # New cart workflow
    cartItems = request.session.get("cart_items", [])
    logger.debug("cartItems: {0}".format(cartItems))
    for item in cartItems:
        if str(item) == str(id):
            cart = Cart.objects.get(id=id)
            cart.delete()
            deleted = True
    if not deleted:
        return abort(404, "Cart ID not in session")
    return success()


def cartDone(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/done.html", context)
