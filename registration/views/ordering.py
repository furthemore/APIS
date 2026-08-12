import json
import logging

from django.core.signing import TimestampSigner
from django.http import JsonResponse
from idempotency_key.decorators import idempotency_key

from registration import mqtt, tasks
from registration.forms import OrderForm
from registration.models import *
from registration.payments import charge_payment

from . import cart, common

logger = logging.getLogger(__name__)


def do_checkout(
    billingData,
    total,
    discount,
    cartItems,
    orderItems,
    donationOrg,
    donationCharity,
    request=None,
):
    event = Event.objects.get(default=True)
    reference = common.get_unique_confirmation_token(Order)

    form = OrderForm(
        collect_billing_address=event.collectBillingAddress,
        data={
            "total": Decimal(total),
            "reference": reference,
            "discount": discount,
            "orgDonation": donationOrg,
            "charityDonation": donationCharity,
            "billingName": " ".join(
                [billingData.get(k) for k in ["cc_firstname", "cc_lastname"]]
            ),
            "billingAddress1": billingData.get("address1"),
            "billingAddress2": billingData.get("address2"),
            "billingCity": billingData.get("city"),
            "billingState": billingData.get("state"),
            "billingCountry": billingData.get("country"),
            "billingEmail": billingData.get("email"),
            "billingPostal": billingData.get("postal"),
        },
    )

    if not form.is_valid():
        return (
            False,
            {"errors": [{"code": f"{k} - {v}"} for k, v in form.errors.items()]},
            None,
        )

    order: Order = form.save(commit=False)

    status, response = charge_payment(order, billingData, request)

    if status:
        order.save()

        if cartItems:
            for item in cartItems:
                order_item = cart.saveCart(item)
                order_item.order = order
                order_item.save()
        elif orderItems:
            for order_item in orderItems:
                order_item.order = order
                order_item.save()

        if discount:
            discount.used = discount.used + 1
            discount.save()
        return True, {"errors": []}, order

    return False, response, order


def doZeroCheckout(discount, cartItems, orderItems):
    billingName = ""
    billingEmail = ""
    if cartItems:
        attendee = json.loads(cartItems[0].formData)["attendee"]
        billingName = "{firstName} {lastName}".format(**attendee)
        billingEmail = attendee["email"]
    elif orderItems:
        attendee = orderItems[0].badge.attendee
        billingName = "{0} {1}".format(attendee.firstName, attendee.lastName)
        billingEmail = attendee.email

    reference = common.get_unique_confirmation_token(Order)

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
            orderItem = cart.saveCart(item)
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


def get_order_item_option_total(options):
    optionTotal = 0
    for option in options:
        if option.option.optionExtraType == "int":
            if option.optionValue:
                optionTotal += option.option.optionPrice * Decimal(option.optionValue)
        else:
            optionTotal += option.option.optionPrice
    return optionTotal


def get_discount_total(disc, subtotal):
    try:
        discount = Discount.objects.get(codeName=disc)
    except Discount.DoesNotExist:
        return 0
    if discount.isValid():
        if discount.amountOff:
            return discount.amountOff
        elif discount.percentOff:
            return Decimal(float(subtotal) * float(discount.percentOff) / 100)
    return 0


def get_total(cartItems, orderItems, disc=""):
    total = 0
    total_discount = 0
    if not cartItems and not orderItems:
        return 0, 0

    for item in cartItems:
        post_data = json.loads(item.formData)
        pdp = post_data["priceLevel"]
        price_level = PriceLevel.objects.get(id=pdp["id"])
        item_total = price_level.basePrice

        options = pdp["options"]
        item_total += getCartItemOptionTotal(options)

        if disc:
            discount = get_discount_total(disc, item_total)
            total_discount += discount
            item_total -= discount

        if item_total > 0:
            total += item_total

    for item in orderItems:
        item_sub_total = item.priceLevel.basePrice
        eff_level = item.badge.effectiveLevel()

        if eff_level:
            item_total = item_sub_total - eff_level.basePrice
        else:
            item_total = item_sub_total

        item_total += get_order_item_option_total(item.attendeeoptions_set.all())

        if disc:
            discount = get_discount_total(disc, item_total)
            total_discount += discount
            item_total -= discount

        if item_total > 0:
            total += item_total

    return total, total_discount


def apply_discount(request):
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


def add_attendee_to_assistant(request, attendee):
    assistant_id = request.session.get("assistant_id")
    if assistant_id:
        logger.info(
            "Linking attendee to dealer assistant",
            extra={"assistant_id": assistant_id, "attendee_id": attendee.id},
        )
        try:
            assistant = DealerAsst.objects.get(pk=assistant_id)
            assistant.attendee = attendee
            assistant.save()
        except DealerAsst.DoesNotExist:
            pass


@idempotency_key(optional=False)
def checkout(request):
    event = Event.objects.get(default=True)
    session_items = request.session.get("cart_items", [])
    cart_items = list(Cart.objects.filter(id__in=session_items))
    order_items = request.session.get("order_items", [])
    pdisc = request.session.get("discount", "")

    # Safety valve (in case session times out before checkout is complete)
    if len(session_items) == 0 and len(order_items) == 0:
        return common.abort(
            400, "Session expired or no session is stored for this client"
        )

    try:
        post_data = json.loads(request.body)
    except ValueError:
        logger.warning("Unable to decode JSON for checkout()")
        return common.abort(400, "Unable to parse input options")

    discount = Discount.objects.filter(codeName=pdisc)
    if discount.count() > 0 and discount.first().isValid():
        discount = discount.first()
    else:
        discount = None

    if order_items:
        order_items = list(OrderItem.objects.filter(id__in=order_items))

    subtotal, _ = get_total(cart_items, order_items, discount)

    if not cart_items and not order_items:
        return common.abort(400, "There is nothing in your cart!")

    if subtotal == 0:
        status, message, order = doZeroCheckout(discount, cart_items, order_items)
        if not status:
            return common.abort(400, message)

        existing_order_item = order.orderitem_set.first()
        if existing_order_item:
            add_attendee_to_assistant(request, existing_order_item.badge.attendee)
        common.clear_session(request)
        tasks.send_registration_email_task.delay(order.id, order.billingEmail)
        return common.success()

    porg = Decimal(post_data.get("orgDonation") or "0.00")
    pcharity = Decimal(post_data.get("charityDonation") or "0.00")
    pbill = post_data["billingData"]

    if porg < 0:
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity

    onsite = post_data["onsite"]
    if onsite:
        reference = common.get_unique_confirmation_token(Order)
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

        if cart_items:
            for item in cart_items:
                order_item = cart.saveCart(item)
                order_item.order = order
                order_item.save()

        if discount:
            discount.used = discount.used + 1
            discount.save()

        status = True
        message = "Onsite success"
    else:
        status, message, order = do_checkout(
            pbill, total, discount, cart_items, order_items, porg, pcharity, request
        )

    if status:
        existing_order_item = order.orderitem_set.first()
        if existing_order_item:
            add_attendee_to_assistant(request, existing_order_item.badge.attendee)
        # Delete cart when done
        cart_items = Cart.objects.filter(id__in=session_items)
        cart_items.delete()
        common.clear_session(request)
        tasks.send_registration_email_task.delay(order.id, order.billingEmail)

        notify_terminal(request, order)

        return common.success()
    else:
        return common.abort(400, message)


def deleteOrderItem(id):
    orderItems = OrderItem.objects.filter(id=id)
    if orderItems.count() == 0:
        return
    orderItem = orderItems.first()
    orderItem.badge.attendee.delete()
    orderItem.badge.delete()
    orderItem.delete()


def cancel_order(request):
    # (DEPRECATED) XXX [Is it actually? Button still hooked up in frontend -R]
    # remove order from session
    order = request.session.get("order_items", [])
    for item in order:
        deleteOrderItem(item)
    # Delete carts
    sessionItems = request.session.get("cart_items", [])
    cartItems = Cart.objects.filter(id__in=sessionItems)
    cartItems.delete()
    # Clear session values
    common.clear_session(request)
    return common.success()


def notify_terminal(request, order):
    try:
        associated_terminal = request.COOKIES.get("terminal-token")
        if associated_terminal:
            signer = TimestampSigner()
            data_obj = signer.unsign_object(associated_terminal, max_age=60 * 30)
            # We only need one badge ID as onsite will automatically add all
            # badges attached to the order.
            order_item = OrderItem.objects.filter(order_id=order.id).first()
            if order_item:
                mqtt.send_mqtt_message(
                    mqtt.get_topic(
                        "web/registration/completed", name=data_obj["terminal"]
                    ),
                    {"badgeId": order_item.badge_id},
                )
    except Exception:
        logger.warning(
            "Could not use terminal-token for post-checkout notification", exc_info=True
        )
