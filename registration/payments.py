import json
import logging
import uuid

from django.conf import settings
from square.client import Client

from .models import *

client = Client(
    access_token=settings.SQUARE_ACCESS_TOKEN,
    environment=settings.SQUARE_ENVIRONMENT,
)
payments_api = client.payments
refunds_api = client.refunds
orders_api = client.orders

logger = logging.getLogger("registration.payments")


def get_idempotency_key(request=None):
    if request:
        header_key = request.META.get("IDEMPOTENCY_KEY")
        if header_key:
            return header_key
    return str(uuid.uuid4())


def charge_payment(order, cc_data, request=None):
    """
    Returns two variabies:
        success - general success flag
        message - type of failure.
    """

    idempotency_key = get_idempotency_key(request)
    converted_total = int(order.total * 100)

    amount = {"amount": converted_total, "currency": settings.SQUARE_CURRENCY}

    order.billingPostal = cc_data["postal"]
    billing_address = {
        "postal_code": cc_data["postal"],
    }

    try:
        billing_address.update(
            {
                "address_line_1": cc_data["address1"],
                "address_line_2": cc_data["address2"],
                "locality": cc_data["city"],
                "administrative_district_level_1": cc_data["state"],
                "postal_code": cc_data["postal"],
                "country": cc_data["country"],
                "buyer_email_address": cc_data["email"],
                "first_name": cc_data["cc_firstname"],
                "last_name": cc_data["cc_lastname"],
            }
        )
    except KeyError as e:
        logger.debug("One or more billing address field omited - skipping")

    body = {
        "idempotency_key": idempotency_key,
        "source_id": cc_data["source_id"],
        "autocomplete": True,
        "amount_money": amount,
        "reference_id": order.reference,
        "billing_address": billing_address,
        "location_id": settings.SQUARE_LOCATION_ID,
    }

    if "verificationToken" in cc_data:
        body["verificationToken"] = cc_data["verificationToken"]

    logger.debug("---- Begin Transaction ----")
    logger.debug(body)

    api_response = payments_api.create_payment(body)

    logger.debug("---- Charge Submitted ----")
    logger.debug(api_response)

    # Square still returns data for failed payments
    order.apiData = api_response.body

    if "payment" in api_response.body:
        order.lastFour = api_response.body["payment"]["card_details"]["card"]["last_4"]

    if api_response.is_success():
        order.status = Order.COMPLETED
        order.notes = "Square: #" + api_response.body["payment"]["id"][:4]
        order.save()

    elif api_response.is_error():
        logger.debug(api_response.errors)
        message = api_response.errors
        logger.debug("---- Transaction Failed ----")
        order.status = Order.FAILED
        order.save()
        return False, {"errors": message}

    logger.debug("---- End Transaction ----")

    return True, api_response.body


def format_errors(errors):
    error_string = ""
    for error in errors:
        error_string += "{e[category]} - {e[code]}: {e[detail]}\n".format(e=error)
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
    payments_response = payments_api.get_payment(payment_id)

    payment = payments_response.body.get("payment")
    if payments_response.is_success():
        api_data["payment"] = payment
        try:
            order.lastFour = api_data["payment"]["card_details"]["card"]["last_4"]
        except KeyError:
            logger.warning("Unable to update last_4 details for order")
        status = payment.get("status")
        if status == "COMPLETED":
            order.status = Order.COMPLETED
            order_total = payment["total_money"]["amount"]
        elif status == "FAILED":
            order.status = Order.FAILED
        elif status == "APPROVED":
            # Payment was only captured, approved, and never settled (not usually what we do)
            # https://developer.squareup.com/docs/payments-api/overview#payments-api-workflow
            order.status = Order.CAPTURED
            order_total = payment["total_money"]["amount"]
        elif status == "CANCELED":
            order.status = Order.FAILED
    else:
        return False, format_errors(payments_response.errors)

    # FIXME: Payments API call includes references to any refunds associated with that payment in `refund_ids`
    # We should use that here instead.
    refunds = []
    refund_errors = []
    refunded_money = payment.get("refunded_money")

    if refunded_money:
        order_total -= refunded_money["amount"]
    refund_ids = payment.get("refund_ids", [])

    stored_refunds = api_data.get("refunds")
    # Keep any potentially pending refunds that may fail (which wouldn't show up in payment.refund_ids)
    if stored_refunds:
        stored_refund_ids = [
            refund["id"] for refund in stored_refunds if refund["id"] not in refund_ids
        ]
        refund_ids.extend(stored_refund_ids)

    for refund_id in refund_ids:
        refunds_response = refunds_api.get_payment_refund(refund_id)

        if refunds_response.is_success():
            refund = refunds_response.body.get("refund")
            if refund:
                refunds.append(refund)
                status = refund.get("status")
                if status == "COMPLETED":
                    order.status = Order.REFUNDED
                elif status == "PENDING":
                    order.status = Order.REFUND_PENDING
        else:
            refund_errors.append(format_errors(payments_response.errors))

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


def process_webhook_refund_updated(notification):
    # Find matching order, if any:
    payment_id = notification.body["data"]["object"]["payment_id"]
    try:
        order = Order.objets.get(apiData__payment__id=payment_id)
    except Order.DoesNotExist:
        logger.warning(
            f"Got webhook for refund.update on payment.id = {payment_id}, but found no corresponding payment."
        )
        return False

    stored_refunds = order.apiData["refunds"]
    refund = notification.body["data"]["object"]["refund"]
    if refund:
        # Check if refund has already been stored (Refund created internally), and update in-place
        order.apiData["refunds"].append(refund)
        status = refund.get("status")
        if status == "COMPLETED":
            order.status = Order.REFUNDED
        elif status == "PENDING":
            order.status = Order.REFUND_PENDING


def process_webhook_refund_created(notification):
    pass


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

    body = {
        "payment_id": payment_id,
        "idempotency_key": str(uuid.uuid4()),
        "amount_money": {
            "amount": converted_amount,
            "currency": settings.SQUARE_CURRENCY,
        },
    }
    if reason:
        body["reason"] = reason

    result = refunds_api.refund_payment(body)
    logger.debug(result.body)

    if result.is_error():
        errors = format_errors(result.errors)
        logger.error("Error in square refund: {0}".format(errors))
        return False, errors

    stored_refunds = api_data.get("refunds")
    if stored_refunds is None:
        stored_refunds = []

    status = result.body["refund"]["status"]
    stored_refunds.append(result.body["refund"])
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


def get_payments_from_order_id(order_id):
    """
    Returns a list of payment IDs (tenders) from the serverTransactionId
    returned from the POS SDK.

    :param order_id:
    :return: list of payment IDs, or None if there was an error
    """

    body = {
        "order_ids": [
            order_id,
        ],
        "location_id": settings.SQUARE_LOCATION_ID,
    }

    result = orders_api.batch_retrieve_orders(body)

    if result.is_success():
        if result.body:
            tenders = result.body["orders"][0]["tenders"]
            payment_ids = [payment["id"] for payment in tenders]
            return payment_ids
        else:
            return []

    elif result.is_error():
        logger.error(
            "There was a problem while fetching order id {0} from Square:".format(
                order_id
            )
        )
        logger.error(format_errors(result.errors))
        return None


def process_webhook_refund_update(notification) -> bool:
    # Find matching order based on refund ID:
    refund_id = notification.request_body["data"]["id"]
    try:
        order = Order.objects.get(apiData__refunds__contains=[{"id": refund_id}])
    except Order.DoesNotExist:
        logger.warning(f"Got refund.updated webhook update for a refund id not found: {refund_id}")
        return False

    webhook_refund = notification.request_body["data"]["object"]["refund"]

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
# vim: ts=4 sts=4 sw=4 expandtab smartindent


def process_webhook_refund_created(notification) -> bool:
    # Find matching order based on refund ID:
    refund_id = notification.request_body["data"]["id"]
    webhook_refund = notification.request_body["data"]["object"]["refund"]
    payment_id = webhook_refund["payment_id"]
    try:
        order = Order.objects.get(apiData__payment={"id": payment_id})
    except Order.DoesNotExist:
        logger.warning(f"Got refund.created webhook update for a payment id not found: {payment_id}")
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
