import json
import logging
from datetime import datetime

from django.shortcuts import render

from registration.models import *

from . import common, ordering
from .attendee import check_ban_list

logger = logging.getLogger(__name__)


def get_cart(request):
    sessionItems = request.session.get("cart_items", [])
    sessionOrderItems = request.session.get("order_items", [])
    discount = request.session.get("discount", "")
    event = Event.objects.get(default=True)
    if not sessionItems and not sessionOrderItems:
        context = {"orderItems": [], "total": 0, "discount": {}, "event": event}
        request.session.flush()
    elif sessionOrderItems:
        orderItems = list(OrderItem.objects.filter(id__in=sessionOrderItems))
        if discount:
            discount = Discount.objects.filter(codeName=discount)
            if discount.count() > 0:
                discount = discount.first()
        total, total_discount = ordering.get_total([], orderItems, discount)

        hasMinors = False
        for item in orderItems:
            if item.badge.isMinor():
                item.isMinor = True
                hasMinors = True
                break

        paid_total = item.badge.paidTotal()

        context = {
            "event": event,
            "orderItems": orderItems,
            "total": total,
            "total_discount": total_discount,
            "paid_total": paid_total,
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
        total, total_discount = ordering.get_total(cartItems, [], discount)

        hasMinors = False
        for idx, cart in enumerate(cartItems):
            cartJson = json.loads(cart.formData)
            pda = cartJson["attendee"]
            event = Event.objects.get(name=cartJson["event"])
            evt = event.eventStart
            tz = timezone.get_current_timezone()
            try:
                birthdate = tz.localize(datetime.strptime(pda["birthdate"], "%Y-%m-%d"))
            except ValueError:
                logger.warning(
                    f"The required field 'birthdate' is not well-formed (got '{pda['birthdate']}')"
                )
                logger.warning(f"Removing malformed cart from session: {cart}")
                request.session["cart_items"].pop(idx)
                cart.delete()
                del cartItems[idx]
                continue

            age_at_event = (
                evt.year
                - birthdate.year
                - ((evt.month, evt.day) < (birthdate.month, birthdate.day))
            )
            pda["isMinor"] = False
            if age_at_event < 18:
                pda["isMinor"] = True
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
        preferredName=pda.get("preferredName", ""),
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
            attendeeOption.save()
        else:
            if option["value"] != "":
                attendeeOption = AttendeeOptions(
                    option=plOption, orderItem=orderItem, optionValue=option["value"]
                )
                attendeeOption.save()

    cart.transferedDate = timezone.now()
    cart.save()

    return orderItem


def add_to_cart(request):
    """
    Create attendee from request post.
    """
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        return common.abort(400, "Unable to decode JSON body")

    event = Event.objects.get(default=True)

    try:
        pda = postData["attendee"]
        pda["firstName"]
        pda["lastName"]
        pda["email"]
    except KeyError:
        return common.abort(400, "Required parameters not found in POST body")

    try:
        datetime.strptime(pda["birthdate"], "%Y-%m-%d")
    except ValueError:
        return common.abort(
            400,
            f"The required field 'birthdate' is not well-formed (got '{pda['birthdate']}')",
        )

    banCheck = check_ban_list(pda["firstName"], pda["lastName"], pda["email"])
    if banCheck:
        logger.error(f"***ban list registration attempt: {pda['email']}***")
        registrationEmail = common.get_registration_email()
        return common.abort(
            403,
            f"We are sorry, but you are unable to register for {event}. If you have any questions, or would like "
            f"further information or assistance, please contact Registration at {registrationEmail}",
        )

    cart = Cart(
        form=Cart.ATTENDEE,
        formData=request.body.decode("utf-8"),
        formHeaders=common.get_request_meta(request),
    )
    cart.save()

    # add attendee to session order
    cartItems = request.session.get("cart_items", [])
    cartItems.append(cart.id)
    request.session["cart_items"] = cartItems
    return common.success()


def remove_from_cart(request):
    # locate attendee in session order
    deleted = False
    order = request.session.get("order_items", [])
    try:
        postData = json.loads(request.body)
    except ValueError as e:
        return common.abort(400, "Unable to decode JSON parameters")
    if "id" not in list(postData.keys()):
        return common.abort(400, "Required parameter `id` not specified")
    id = postData["id"]

    # Old workflow
    common.logger.debug("order_items: {0}".format(order))
    common.logger.debug("delete order from session: {0}".format(id))
    if int(id) in order:
        order.remove(int(id))
        deleted = True
        request.session["order_items"] = order
        return common.success()

    # New cart workflow
    cartItems = request.session.get("cart_items", [])
    common.logger.debug("cartItems: {0}".format(cartItems))
    for item in cartItems:
        if str(item) == str(id):
            cart = Cart.objects.get(id=id)
            cart.delete()
            deleted = True
    if not deleted:
        return common.abort(404, "Cart ID not in session")
    return common.success()


def cart_done(request):
    event = Event.objects.get(default=True)
    context = {"event": event}
    return render(request, "registration/done.html", context)
