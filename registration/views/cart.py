import json
import logging
from datetime import datetime

from django.shortcuts import render

from registration.forms import AttendeeForm, BadgeForm
from registration.models import *
from registration.services import CreateAttendeeOptions

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
                birthdate = datetime.strptime(pda["birthdate"], "%Y-%m-%d").replace(
                    tzinfo=tz
                )
            except ValueError:
                logger.warning(
                    "Malformed birthdate in cart, removing from session",
                    extra={"cart_id": cart.id},
                )
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
    post_data = json.loads(cart.formData)
    pda = post_data["attendee"]
    pdp = post_data["priceLevel"]
    evt = post_data["event"]

    event = Event.objects.get(name=evt)

    form = AttendeeForm.from_pda(pda, event)
    attendee: Attendee = form.save()

    badge = Badge.objects.create(
        badgeName=pda["badgeName"],
        event=event,
        attendee=attendee,
        signature_svg=pda.get("signature_svg"),
        signature_bitmap=pda.get("signature_bitmap"),
    )

    price_level = PriceLevel.objects.get(id=int(pdp["id"]))

    via = "WEB"
    if post_data["attendee"].get("onsite", False):
        via = "ONSITE"

    order_item = OrderItem.objects.create(
        badge=badge, priceLevel=price_level, enteredBy=via
    )

    CreateAttendeeOptions(order_item).save_options(pdp["options"])

    cart.transferedDate = timezone.now()
    cart.save()

    return order_item


def add_to_cart(request):
    """
    Create attendee from request post.
    """
    try:
        post_data = json.loads(request.body)
    except ValueError:
        return common.abort(400, "Unable to decode JSON body")

    event = Event.objects.get(default=True)

    pda = post_data["attendee"]

    attendee_form = AttendeeForm.from_pda(pda, event)
    if not attendee_form.is_valid():
        return common.abort(400, attendee_form.errors.as_text())

    badge_form = BadgeForm(
        data={
            "badgeName": pda.get("badgeName"),
            "signature_svg": pda.get("signature_svg"),
            "signature_bitmap": pda.get("signature_bitmap"),
        }
    )
    if not badge_form.is_valid():
        return common.abort(400, badge_form.errors.as_text())

    pda = attendee_form.cleaned_data

    if check_ban_list(pda["firstName"], pda["lastName"], pda["email"]):
        logger.warning(
            "Ban list registration attempt blocked",
            extra={"email": pda["email"], "first_name": pda["firstName"], "last_name": pda["lastName"]},
        )
        registrationEmail = common.get_registration_email()
        return common.abort(
            403,
            f"We are sorry, but you are unable to register for {event}. If you have any questions, or would like "
            f"further information or assistance, please contact Registration at {registrationEmail}",
        )

    cart = Cart.objects.create(
        form=Cart.ATTENDEE,
        formData=request.body.decode("utf-8"),
        formHeaders=common.get_request_meta(request),
    )

    # add attendee to session order
    cart_items = request.session.get("cart_items", [])
    cart_items.append(cart.id)
    request.session["cart_items"] = cart_items

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
    logger.debug("Removing item from cart", extra={"item_id": id, "order_items": order})
    if int(id) in order:
        order.remove(int(id))
        deleted = True
        request.session["order_items"] = order
        return common.success()

    # New cart workflow
    cartItems = request.session.get("cart_items", [])
    logger.debug("Checking cart_items for removal", extra={"cart_items": cartItems, "item_id": id})
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
