import logging
import uuid
from datetime import datetime
from typing import List, Optional

from django.conf import settings
from prometheus_client import Histogram
from square import Square
from square.core.api_error import ApiError
from square.environment import SquareEnvironment
from square.requests.address import AddressParams
from square.requests.device_checkout_options import DeviceCheckoutOptionsParams
from square.requests.money import MoneyParams
from square.requests.order import OrderParams
from square.requests.order_line_item import OrderLineItemParams
from square.requests.order_line_item_applied_discount import (
    OrderLineItemAppliedDiscountParams,
)
from square.requests.order_line_item_discount import OrderLineItemDiscountParams
from square.requests.order_source import OrderSourceParams
from square.requests.receipt_options import ReceiptOptionsParams
from square.requests.terminal_action import TerminalActionParams
from square.requests.terminal_checkout import TerminalCheckoutParams
from square.types.create_terminal_checkout_response import (
    CreateTerminalCheckoutResponse,
)
from square.types.device import Device
from square.types.error import Error
from square.types.payment import Payment

from . import emails
from .models import *

SQUARE_REQUESTS = Histogram(
    "square_requests", "HTTP requests to Square API", ["endpoint"]
)

logger = logging.getLogger("registration.payments")

environment = SquareEnvironment.PRODUCTION
if settings.SQUARE_ENVIRONMENT == "sandbox":
    environment = SquareEnvironment.SANDBOX

client = Square(token=settings.SQUARE_ACCESS_TOKEN, environment=environment)


def get_idempotency_key(request=None):
    if request:
        header_key = request.META.get("IDEMPOTENCY_KEY")
        if header_key:
            return header_key
    return str(uuid.uuid4())


def charge_payment(order: Order, cc_data: dict, request=None):
    """
    Returns two variabies:
        success - general success flag
        message - type of failure.
    """

    idempotency_key = get_idempotency_key(request)
    converted_total = int(order.total * 100)

    amount = MoneyParams(amount=converted_total, currency=settings.SQUARE_CURRENCY)

    order.billingPostal = cc_data["postal"]

    try:
        billing_address = AddressParams(
            address_line1=cc_data["address1"],
            address_line2=cc_data["address2"],
            locality=cc_data["city"],
            administrative_district_level1=cc_data["state"],
            postal_code=cc_data["postal"],
            country=cc_data["country"],
            first_name=cc_data["cc_firstname"],
            last_name=cc_data["cc_lastname"],
        )
    except KeyError:
        logger.debug("One or more billing address field omited - skipping")
        billing_address = AddressParams(postal_code=cc_data["postal"])

    logger.debug("---- Begin Transaction ----")

    try:
        with SQUARE_REQUESTS.labels(endpoint="create_payment").time():
            api_response = client.payments.create(
                idempotency_key=idempotency_key,
                source_id=cc_data["source_id"],
                autocomplete=True,
                amount_money=amount,
                reference_id=order.reference,
                billing_address=billing_address,
                location_id=settings.SQUARE_LOCATION_ID,
                verification_token=cc_data.get("verificationToken"),
                buyer_email_address=cc_data.get("email"),
            )
    except ApiError as e:
        logger.debug(e.errors)
        logger.error("---- Transaction Failed ----")
        order.status = Order.FAILED
        order.apiData = e.body
        order.save()
        return False, e.body

    logger.debug("---- Charge Submitted ----")

    # Square still returns data for failed payments
    order.apiData = api_response.model_dump()

    if (
        api_response.payment
        and api_response.payment.id
        and api_response.payment.status != "FAILED"
    ):
        if api_response.payment.card_details and api_response.payment.card_details.card:
            order.lastFour = str(api_response.payment.card_details.card.last4)

        logger.debug("---- End Transaction ----")
        order.status = Order.COMPLETED
        order.notes = "Square: #" + api_response.payment.id[:4]
        order.save()
        return True, None
    else:
        logger.debug(api_response.errors)
        logger.debug("---- Transaction Failed ----")
        order.status = Order.FAILED
        order.save()
        return False, {"errors": [e.model_dump() for e in api_response.errors or []]}


def format_errors(errors: List[Error]):
    error_string = ""
    for error in errors:
        error_string += f"{error.category} - {error.code}: {error.detail}\n"
    return error_string


def refresh_payment(order, store_api_data=None):
    # Function raises ValueError if there's a problem decoding the stored data
    if store_api_data:
        api_data = store_api_data
    else:
        api_data = order.apiData
        if not api_data:
            logger.warning("No order data yet for {0}".format(order.reference))
            return False, "No order data yet for {0}".format(order.reference)
    order_total = 0

    try:
        payment_id = api_data["payment"]["id"]
    except KeyError:
        logger.warning("Refresh payment: MISSING_PAYMENT_ID")
        return False, "MISSING_PAYMENT_ID"

    try:
        with SQUARE_REQUESTS.labels(endpoint="get_payment").time():
            payments_response = client.payments.get(payment_id)
    except ApiError as e:
        return False, format_errors(e.errors)

    if payments_response.payment:
        api_data["payment"] = payments_response.payment.model_dump()
        order_total = update_order_payment_data(
            order, order_total, payments_response.payment
        )
    else:
        return False, format_errors(payments_response.errors or [])

    # FIXME: Payments API call includes references to any refunds associated with that payment in `refund_ids`
    # We should use that here instead.
    refunds = []
    refund_errors = []
    refunded_money = payments_response.payment.refunded_money

    if refunded_money:
        order_total -= refunded_money.amount
    refund_ids = payments_response.payment.refund_ids or []

    stored_refunds = api_data.get("refunds")
    # Keep any potentially pending refunds that may fail (which wouldn't show up in payment.refund_ids)
    if stored_refunds:
        stored_refund_ids = [
            refund["id"] for refund in stored_refunds if refund["id"] not in refund_ids
        ]
        refund_ids.extend(stored_refund_ids)

    for refund_id in refund_ids:
        try:
            with SQUARE_REQUESTS.labels(endpoint="get_payment_refund").time():
                refunds_response = client.refunds.get(refund_id)

                if refunds_response.errors:
                    refund_errors.append(format_errors(refunds_response.errors))
                elif refunds_response.refund:
                    refunds.append(refunds_response.refund.model_dump())
                    status = refunds_response.refund.status
                    if status == "COMPLETED":
                        order.status = Order.REFUNDED
                    elif status == "PENDING":
                        order.status = Order.REFUND_PENDING
        except ApiError as e:
            refund_errors.append(format_errors(e.errors))

    api_data["refunds"] = refunds

    if refund_errors:
        return False, "; ".join(refund_errors)

    order.apiData = api_data
    order.total = Decimal(order_total) / 100

    if order.orgDonation + order.charityDonation > order.total:
        order.orgDonation = 0
        order.charityDonation = order.total
        message = "Refunded order has caused charity and organization donation amounts to reset."
        logger.warning(message)
        order.notes += "\n{0}: {1}".format(timezone.now(), message)
        order.save()
        return False, message

    order.save()
    return True, None


def update_order_payment_data(order: Order, order_total: int, payment: Payment) -> int:
    try:
        order.lastFour = payment.card_details.card.last4
    except KeyError:
        logger.warning("Unable to update last_4 details for order")
    status = payment.status
    if status == "COMPLETED":
        order.status = Order.COMPLETED
        order_total = payment.total_money.amount
    elif status == "FAILED":
        order.status = Order.FAILED
    elif status == "APPROVED":
        # Payment was only captured, approved, and never settled (not usually what we do)
        # https://developer.squareup.com/docs/payments-api/overview#payments-api-workflow
        order.status = Order.CAPTURED
        order_total = payment.total_money.amount
    elif status == "CANCELED":
        order.status = Order.FAILED
    return order_total


def refund_payment(order, amount, reason=None, request=None):
    if order.status == Order.FAILED:
        return False, "Failed orders cannot be refunded."
    if order.billingType == Order.CREDIT:
        result, message = refund_card_payment(order, amount, reason, request=None)
        return result, message
    if order.billingType == Order.CASH:
        result, message = refund_cash_payment(order, amount, reason)
        return result, message
    if order.billingType == Order.COMP:
        return False, "Comped orders cannot be refunded."
    if order.billingType == Order.UNPAID:
        return False, "Unpaid orders cannot be refunded."
    return False, "Not sure how to refund order type {0}!".format(order.billingType)


def refund_cash_payment(order, amount, reason=None):
    # Change order status
    order.status = Order.REFUNDED
    order.notes += "\nRefund issued {0}: {1}".format(timezone.now(), reason)

    # Reset order total
    order.total -= amount
    order.save()

    # Record cashdrawer withdraw
    withdraw = Cashdrawer(action=Cashdrawer.TRANSACTION, total=-amount)
    withdraw.save()
    return True, None


def refund_card_payment(order, amount, reason=None, request=None):
    api_data = order.apiData
    payment_id = api_data["payment"]["id"]
    converted_amount = int(amount * 100)

    try:
        with SQUARE_REQUESTS.labels(endpoint="refund_payment").time():
            api_response = client.refunds.refund_payment(
                idempotency_key=get_idempotency_key(request),
                payment_id=payment_id,
                amount_money=MoneyParams(
                    amount=converted_amount, currency=settings.SQUARE_CURRENCY
                ),
                reason=reason,
            )
    except ApiError as e:
        errors = format_errors(e.errors)
        logger.error("Error in square refund: {0}".format(errors))
        return False, errors

    if api_response.errors:
        errors = format_errors(api_response.errors)
        logger.error("Error in square refund: {0}".format(errors))
        return False, errors

    stored_refunds = api_data.get("refunds") or []

    status = api_response.refund.status
    stored_refunds.append(api_response.refund.model_dump())
    api_data["refunds"] = stored_refunds
    order.apiData = api_data

    if status == "COMPLETED":
        order.status = Order.REFUNDED
    if status == "PENDING":
        order.status = Order.REFUND_PENDING

    if status in ("COMPLETED", "PENDING"):
        order.total -= amount
        # Reset org & charity donations if the remaining total isn't enough to cover them:
        if order.orgDonation + order.charityDonation > order.total:
            order.orgDonation = 0
            order.charityDonation = order.total
            logger.warning(
                "Refunded order has caused charity and organization donation amounts to reset."
            )
            order.notes += "\nWarning: Refunded order has caused charity and organization donation amounts to reset.\n"

    if status in ("REJECTED", "FAILED"):
        order.status = Order.COMPLETED

    order.save()
    message = "Square refund has been submitted and is {0}".format(status)
    logger.debug(message)
    return True, message


def process_webhook_refund_update(notification: PaymentWebhookNotification) -> bool:
    # Find matching order based on refund ID:
    refund_id = notification.body["data"]["id"]
    try:
        order = Order.objects.get(apiData__refunds__contains=[{"id": refund_id}])
    except Order.DoesNotExist:
        logger.warning(
            f"Got refund.updated webhook update for a refund id not found: {refund_id}"
        )
        return False

    webhook_refund = notification.body["data"]["object"]["refund"]

    output = []
    refunds_list = order.apiData["refunds"]
    for refund in refunds_list:
        if refund["id"] == refund_id:
            output.append(webhook_refund)
        else:
            output.append(refund)

    if webhook_refund["status"] == "COMPLETED":
        order.status = Order.REFUNDED

    order.apiData["refunds"] = output
    order.save()
    return True


def process_webhook_payment_updated(notification: PaymentWebhookNotification) -> bool:
    payment_id = notification.body["data"]["id"]
    try:
        order = Order.objects.get(apiData__payment__id=payment_id)
    except Order.DoesNotExist:
        logger.warning(
            f"Got payment.updated webhook update for a payment id not found: {payment_id}"
        )
        return False

    # Store order update in api data
    payment = Payment.model_validate(notification.body["data"]["object"]["payment"])
    order.apiData["payment"] = payment.model_dump()
    update_order_payment_data(order, 0, payment)
    order.save()
    return True


def process_webhook_refund_created(notification: PaymentWebhookNotification) -> bool:
    # Find matching order based on refund ID:
    refund_id = notification.body["data"]["id"]
    webhook_refund = notification.body["data"]["object"]["refund"]
    payment_id = webhook_refund["payment_id"]
    try:
        order = Order.objects.get(apiData__payment__id=payment_id)
    except Order.DoesNotExist:
        logger.warning(
            f"Got refund.created webhook update for a payment id not found: {payment_id}"
        )
        return False

    # Skip processing if we already have this refund id stored:
    refund_exists = Order.objects.filter(apiData__refunds__contains=[{"id": refund_id}])
    if len(refund_exists) > 0:
        logger.info(f"Refund {refund_id} already exists, skipping processing...")
        return True

    # Store refund in api data

    order.apiData["refunds"].append(webhook_refund)

    status = webhook_refund["status"]
    if status == "COMPLETED":
        order.status = Order.REFUNDED
    if status == "PENDING":
        order.status = Order.REFUND_PENDING

    if status in ("COMPLETED", "PENDING"):
        order.total -= Decimal(webhook_refund["amount_money"]["amount"]) / 100
        # Reset org & charity donations if the remaining total isn't enough to cover them:
        if order.orgDonation + order.charityDonation > order.total:
            order.orgDonation = 0
            order.charityDonation = order.total
            logger.warning(
                "Refunded order has caused charity and organization donation amounts to reset."
            )
            order.notes += "\nWarning: Refunded order has caused charity and organization donation amounts to reset.\n"

    if status in ("REJECTED", "FAILED"):
        order.status = Order.COMPLETED

    order.save()
    return True


def process_webhook_dispute_created_or_updated(
    notification: PaymentWebhookNotification,
) -> bool:
    webhook_dispute = notification.body["data"]["object"]["dispute"]
    payment_id = webhook_dispute["disputed_payment"]["payment_id"]
    try:
        order = Order.objects.get(apiData__payment__id=payment_id)
    except Order.DoesNotExist:
        logger.warning(
            f"Got dispute.created webhook update for a payment id not found: {payment_id}"
        )
        return False

    # Add the dispute API data to the order:
    order.apiData["dispute"] = webhook_dispute
    order.status = Order.DISPUTE_STATUS_MAP[webhook_dispute["state"]]
    if order.status in (Order.DISPUTE_LOST, Order.DISPUTE_ACCEPTED) and (
        order.orgDonation > 0 or order.charityDonation > 0
    ):
        # If we've lost or accepted the dispute, reset charitable donation earmarks:
        order.notes += (
            f"\n\nOriginal charity donation of ${order.charityDonation} and organization donation "
            + f"of ${order.orgDonation} were reset due to lost or accepted dispute state."
        )
        order.orgDonation = 0
        order.charityDonation = 0
    order.save()

    # Place a hold on all new disputed orders, and add attendee to the ban list.  Should only do this once,
    # when the dispute is created (with state EVIDENCE_REQUIRED).
    if webhook_dispute["state"] == "EVIDENCE_REQUIRED":
        dispute_hold = get_hold_type("Chargeback")
        order_items = OrderItem.objects.filter(order=order)
        # Add dispute hold to all attendees on the order
        for oi in order_items:
            attendee = oi.badge.attendee
            attendee.holdType = dispute_hold
            attendee.save()

            # Add all attendees to the ban list
            ban = BanList(
                firstName=attendee.firstName,
                lastName=attendee.lastName,
                email=attendee.email,
                reason=f"Initiated chargeback [APIS {datetime.now().isoformat()}]",
            )

            ban.save()

            # Send an email about it
            emails.send_chargeback_notice_email(order)

    return True


def create_square_order(terminal_name: str, data: dict) -> Optional[str]:
    discounts = []
    line_items = []

    for badge in data["result"]:
        badge_applied_discounts = []

        if badge["discount"]:
            discount = badge["discount"]
            uid = f"discount-{badge['id']}"

            if discount["percent_off"] > 0:
                discounts.append(
                    OrderLineItemDiscountParams(
                        uid=uid,
                        name=f"Discount {discount['name']}",
                        type="FIXED_PERCENTAGE",
                        scope="LINE_ITEM",
                        percentage=str(discount["percent_off"]),
                    )
                )
            elif discount["amount_off"] > 0:
                discounts.append(
                    OrderLineItemDiscountParams(
                        uid=uid,
                        name=f"Discount {discount['name']}",
                        type="FIXED_AMOUNT",
                        scope="LINE_ITEM",
                        amount_money=MoneyParams(
                            amount=int(discount["amount_off"] * 100),
                            currency=settings.SQUARE_CURRENCY,
                        ),
                    )
                )

            badge_applied_discounts.append(
                OrderLineItemAppliedDiscountParams(discount_uid=uid)
            )

        line_items.append(
            OrderLineItemParams(
                uid=f"badge-{badge['id']}",
                name=f"{badge['effectiveLevel']['name']} Badge",
                note=f"Badge Name - {badge['badgeName']}",
                quantity="1",
                item_type="ITEM",
                base_price_money=MoneyParams(
                    amount=int(badge["level_subtotal"] * 100),
                    currency=settings.SQUARE_CURRENCY,
                ),
                applied_discounts=badge_applied_discounts,
            )
        )

    if data["charityDonation"] > 0 or data["orgDonation"] > 0:
        event = Event.objects.get(default=True)

        if data["charityDonation"] > 0:
            line_items.append(
                OrderLineItemParams(
                    uid="donation-charity",
                    name=f"Donation to {event.charity}",
                    quantity="1",
                    item_type="ITEM",
                    base_price_money=MoneyParams(
                        amount=int(data["charityDonation"] * 100),
                        currency=settings.SQUARE_CURRENCY,
                    ),
                )
            )

        if data["orgDonation"] > 0:
            line_items.append(
                OrderLineItemParams(
                    uid="donation-organization",
                    name=f"Donation to {event}",
                    quantity="1",
                    item_type="ITEM",
                    base_price_money=MoneyParams(
                        amount=int(data["orgDonation"] * 100),
                        currency=settings.SQUARE_CURRENCY,
                    ),
                )
            )

    try:
        with SQUARE_REQUESTS.labels(endpoint="create_order").time():
            api_response = client.orders.create(
                idempotency_key=str(uuid.uuid4()),
                order=OrderParams(
                    location_id=settings.SQUARE_LOCATION_ID,
                    reference_id=data["reference"],
                    source=OrderSourceParams(name=terminal_name),
                    discounts=discounts,
                    line_items=line_items,
                ),
            )
    except ApiError as e:
        logger.error("failed to create order: %s", e.errors)
        return None

    if api_response.order:
        return api_response.order.id
    else:
        logger.error("failed to create order: %s", api_response.errors)
        return None


def print_payment_receipt(
    request, square_device: SquareDevice, payment_id: str
) -> bool:
    try:
        with SQUARE_REQUESTS.labels(endpoint="create_terminal_action").time():
            api_response = client.terminal.actions.create(
                idempotency_key=get_idempotency_key(request),
                action=TerminalActionParams(
                    device_id=square_device.device_id,
                    type="RECEIPT",
                    receipt_options=ReceiptOptionsParams(
                        payment_id=payment_id,
                        print_only=True,
                    ),
                ),
            )
    except ApiError as e:
        logger.error("Could not print receipt: %s", e.errors)
        return False

    if api_response.errors:
        logger.error("Could not print receipt: %s", api_response.errors)
        return False
    else:
        return True


def get_terminals() -> List[Device]:
    api_response = client.devices.list()

    terminals = []
    for device in api_response:
        terminals.append(device)
    return terminals


def prompt_terminal_payment(
    request,
    device_id: str,
    total: int,
    reference: str,
    note: str,
    order_id: Optional[str],
) -> CreateTerminalCheckoutResponse:
    if order_id:
        checkout_note = None
    else:
        checkout_note = note
        order_id = None

    return client.terminal.checkouts.create(
        idempotency_key=get_idempotency_key(request),
        checkout=TerminalCheckoutParams(
            amount_money=MoneyParams(amount=total, currency=settings.SQUARE_CURRENCY),
            reference_id=reference,
            device_options=DeviceCheckoutOptionsParams(device_id=device_id),
            order_id=order_id,
            note=checkout_note,
        ),
    )
