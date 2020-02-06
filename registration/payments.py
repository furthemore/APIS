import logging
import uuid

from django.conf import settings
from square.client import Client

from .models import *

client = Client(
    access_token=settings.SQUARE_ACCESS_TOKEN, environment=settings.SQUARE_ENVIRONMENT,
)
payments_api = client.payments
refunds_api = client.refunds

logger = logging.getLogger("registration.payments")


def charge_payment(order, cc_data):
    """
    Returns two variabies:
        success - general success flag
        message - type of failure.
    """

    idempotency_key = str(uuid.uuid4())
    converted_total = int(order.total * 100)

    amount = {"amount": converted_total, "currency": settings.SQUARE_CURRENCY}

    billing_address = {
        "postal_code": cc_data["card_data"]["billing_postal_code"],
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
        "source_id": cc_data["nonce"],
        "autocomplete": True,
        "amount_money": amount,
        "reference_id": order.reference,
        "billing_address": billing_address,
        "location_id": settings.SQUARE_LOCATION_ID,
    }

    logger.debug("---- Begin Transaction ----")
    logger.debug(body)

    api_response = payments_api.create_payment(body)

    logger.debug("---- Charge Submitted ----")
    logger.debug(api_response)

    # Square still returns data for failed payments
    order.apiData = json.dumps(api_response.body)

    if api_response.is_success():
        order.status = Order.COMPLETED
        order.notes = "Square: #" + api_response.body["payment"]["id"][:4]
        card_details = api_response.body["payment"]["card_details"]
        order.lastFour = "0000"
        if (
            api_response.body["payment"]["source_type"] == "CARD"
            and card_details is not None
        ):
            order.lastFour = card_details["card"].get("last_4")
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
        error_string += u"{e[category]} - {e[code]}: {e[detail]}\n".format(e=error)
    return error_string


def refresh_payment(order):
    # Function raises ValueError if there's a problem decoding the stored data
    api_data = json.loads(order.apiData)
    order_total = 0

    payment_id = api_data["payment"]["id"]
    payments_response = payments_api.get_payment(payment_id)

    payment = payments_response.body.get("payment")
    if payments_response.is_success():
        api_data["payment"] = payment
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
    print(refunded_money, order_total)
    if refunded_money:
        order_total -= refunded_money["amount"]
    refund_ids = payment.get("refund_ids")

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
                elif (
                    status in ("REJECTED", "FAILED") and order.status != Order.COMPLETED
                ):
                    pass
        else:
            refund_errors.append(format_errors(payments_response.errors))

    api_data["refunds"] = refunds

    if refund_errors:
        return False, "; ".join(refund_errors)

    order.apiData = json.dumps(api_data)
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


def refund_payment(order, amount, reason=None, request=None):
    if order.billingType == Order.CREDIT:
        result, message = refund_card_payment(order, amount, reason, request=None)
    if order.billingType == Order.CASH:
        result, message = refund_cash_payment(order, amount, reason)
    return result, message
    if order.billingType == Order.COMP:
        return False, "Comped orders cannot be refunded."
    if order.billingType == Order.FAILED:
        return False, "Failed orders cannot be refunded."
    return False, "Not sure how to refund order type {0}!".format(order.billingType)


def refund_cash_payment(order, amount, reason=None):
    return False, "Unimplimented"


def refund_card_payment(order, amount, reason=None, request=None):
    api_data = json.loads(order.apiData)
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

    stored_refunds = api_data.get("refunds")
    if stored_refunds is None:
        stored_refunds = []

    status = result.body["refund"]["status"]
    stored_refunds.append(result.body["refund"])
    api_data["refunds"] = stored_refunds
    order.apiData = json.dumps(api_data)

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
    if result.is_success():
        message = "Square refund has been submitted and is {0}".format(status)
        logger.debug(message)
        return True, message
    else:
        errors = format_errors(result.errors)
        logger.error("Error in square refund: {0}".format(errors))
        return False, errors


# vim: ts=4 sts=4 sw=4 expandtab smartindent
