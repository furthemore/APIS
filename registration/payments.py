import logging
import uuid

from django.conf import settings
from square.client import Client

from .models import *

client = Client(
    access_token=settings.SQUARE_ACCESS_TOKEN, environment=settings.SQUARE_ENVIRONMENT,
)
payments_api = client.payments

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

    if api_response.is_success():
        card_details = api_response.body["payment"]["card_details"]
        order.lastFour = "0000"
        if (
            api_response.body["payment"]["source_type"] == "CARD"
            and card_details is not None
        ):
            order.lastFour = card_details["card"].get("last_4")
        order.apiData = json.dumps(api_response.body)
        order.notes = "Square: #" + api_response.body["payment"]["id"][:4]
        order.save()
    elif api_response.is_error():
        logger.debug(api_response.errors)
        message = format_errors(api_response.errors)
        logger.debug("---- Transaction Failed ----")
        return False, {"errors": api_response.errors}

    logger.debug("---- End Transaction ----")

    return True, api_response.body


def format_errors(errors):
    error_string = ""
    for error in errors:
        error_string += u"{e[category]} - {e[code]}: {e[detail]}\n".format(e=error)
    return error_string


# vim: ts=4 sts=4 sw=4 expandtab smartindent
