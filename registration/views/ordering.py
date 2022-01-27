import json
import logging
import time

from django.http import JsonResponse
from idempotency_key.decorators import idempotency_key

import registration.emails
from registration.models import *
from registration.payments import charge_payment

from . import cart, common

logger = logging.getLogger(__name__)


def doCheckout(
    billingData, total, discount, cartItems, orderItems, donationOrg, donationCharity, request=None
):
    event = Event.objects.get(default=True)
    reference = common.get_unique_confirmation_token(Order)

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
            common.abort(
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
        common.abort(
            400, "A required field was missing from billingData: {0}".format(e)
        )

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
        return True, "", order

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
    try:
        discount = Discount.objects.get(codeName=disc)
    except Discount.DoesNotExist:
        return 0
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

        if itemTotal > 0:
            total += itemTotal

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
        logger.info(f"Add attendee {attendee} to assistant id: {assistant_id}")
        try:
            assistant = DealerAsst.objects.get(pk=assistant_id)
            assistant.attendee = attendee
            assistant.save()
        except DealerAsst.DoesNotExist:
            pass


@idempotency_key(optional=False)
def checkout(request):
    event = Event.objects.get(default=True)
    sessionItems = request.session.get("cart_items", [])
    cartItems = list(Cart.objects.filter(id__in=sessionItems))
    orderItems = request.session.get("order_items", [])
    pdisc = request.session.get("discount", "")

    # Safety valve (in case session times out before checkout is complete)
    if len(sessionItems) == 0 and len(orderItems) == 0:
        common.abort(400, "Session expired or no session is stored for this client")

    try:
        postData = json.loads(request.body)
    except ValueError as e:
        logger.exception(e)
        logger.error("Unable to decode JSON for checkout()")
        return common.abort(400, "Unable to parse input options")

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
            return common.abort(400, message)

        add_attendee_to_assistant(request, order.orderitem_set.first().badge.attendee)
        common.clear_session(request)
        try:
            registration.emails.send_registration_email(order, order.billingEmail)
        except Exception as e:
            logger.error("Error sending RegistrationEmail - zero sum.")
            logger.exception(e)
            registrationEmail = common.getRegistrationEmail(event)
            return common.abort(
                400,
                "Your payment succeeded but we may have been unable to send you a confirmation email. If you do not "
                "receive one within the next hour, please contact {0} to get your confirmation number.".format(
                    registrationEmail
                ),
            )
        return common.success()

    porg = Decimal(postData.get("orgDonation") or "0.00")
    pcharity = Decimal(postData.get("charityDonation") or "0.00")
    pbill = postData["billingData"]

    if porg < 0:
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity

    onsite = postData["onsite"]
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

        if cartItems:
            for item in cartItems:
                orderItem = cart.saveCart(item)
                orderItem.order = order
                orderItem.save()

        if discount:
            discount.used = discount.used + 1
            discount.save()

        status = True
        message = "Onsite success"
    else:
        status, message, order = doCheckout(
            pbill, total, discount, cartItems, orderItems, porg, pcharity, request
        )

    if status:
        add_attendee_to_assistant(request, order.orderitem_set.first().badge.attendee)
        # Delete cart when done
        cartItems = Cart.objects.filter(id__in=sessionItems)
        cartItems.delete()
        common.clear_session(request)
        try:
            registration.emails.send_registration_email(order, order.billingEmail)
        except Exception as e:
            event = Event.objects.get(default=True)
            registrationEmail = common.getRegistrationEmail(event)

            logger.error("Error sending RegistrationEmail.")
            logger.exception(e)
            return common.abort(
                500,
                "Your payment succeeded but we may have been unable to send you a confirmation email. If you do not "
                "receive one within the next hour, please contact {0} to get your confirmation number.".format(
                    registrationEmail
                ),
            )
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
