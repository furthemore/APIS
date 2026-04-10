import json
import logging
from decimal import Decimal
from typing import TypedDict

from django.conf import settings
from django.http import HttpRequest
from paypalserversdk.configuration import Environment
from paypalserversdk.controllers.orders_controller import OrdersController
from paypalserversdk.controllers.payments_controller import PaymentsController
from paypalserversdk.exceptions.api_exception import ApiException
from paypalserversdk.http.api_response import ApiResponse
from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
from paypalserversdk.logging.configuration.api_logging_configuration import (
    LoggingConfiguration,
    RequestLoggingConfiguration,
    ResponseLoggingConfiguration,
)
from paypalserversdk.models.amount_breakdown import AmountBreakdown
from paypalserversdk.models.amount_with_breakdown import AmountWithBreakdown
from paypalserversdk.models.checkout_payment_intent import CheckoutPaymentIntent
from paypalserversdk.models.item import Item
from paypalserversdk.models.item_category import ItemCategory
from paypalserversdk.models.money import Money
from paypalserversdk.models.order_request import OrderRequest
from paypalserversdk.models.purchase_unit_request import PurchaseUnitRequest
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient
from prometheus_client import Histogram

from .models import *

PAYPAL_REQUESTS = Histogram(
    "paypal_requests", "HTTP requests to Paypal API", ["endpoint"]
)

client = PaypalServersdkClient(
    client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
        o_auth_client_id=settings.PAYPAL_CLIENT_ID,
        o_auth_client_secret=settings.PAYPAL_CLIENT_SECRET,
    ),
    environment=(
        Environment.PRODUCTION
        if settings.PAYPAL_ENVIRONMENT.lower()[0] == "p"
        else Environment.SANDBOX
    ),
    logging_configuration=LoggingConfiguration(
        log_level=logging.INFO,
        request_logging_config=RequestLoggingConfiguration(log_body=settings.DEBUG),
        response_logging_config=ResponseLoggingConfiguration(
            log_headers=settings.DEBUG
        ),
    ),
)

logger = logging.getLogger("registration.paypal_payments")


class TranslatedCartItem(TypedDict):
    name: str
    total: Decimal
    donation: bool


orders_controller: OrdersController = client.orders
payments_controller: PaymentsController = client.payments


def create_unpaid_paypal_order(
    total: str | int | Decimal,
    discount: str | int | Decimal,
    cart_items: list[TranslatedCartItem],
) -> ApiResponse:
    registrations = []
    donations = []
    donation_total = 0
    for item in cart_items:
        pp_item = Item(
            name=item["name"],
            unit_amount=Money(currency_code="USD", value=str(item["total"])),
            quantity=1,
            category=ItemCategory.DIGITAL_GOODS,
        )
        registrations.append(pp_item)
        # TODO: I'd like to separate out donations in this call but even if I
        # break them out into separate purchase units it complains that I'm
        # mixing item categories in a purchase unit when I'm not.
        # if item["donation"]:
        #     pp_item.category = ItemCategory.DONATION
        #     total -= item["total"]
        #     donation_total += item["total"]
        #     donations.append(pp_item)
        # else:
        #     registrations.append(pp_item)

    purchase_units = [
        PurchaseUnitRequest(
            reference_id="registration",
            amount=AmountWithBreakdown(
                currency_code="USD",
                value=str(total),
                breakdown=AmountBreakdown(
                    item_total=Money(currency_code="USD", value=str(total - discount)),
                    discount=Money(currency_code="USD", value=str(discount)),
                ),
            ),
            items=registrations,
        )
    ]

    # for donationItem in donations:
    #     purchase_units.append(PurchaseUnitRequest(
    #         reference_id="donations",
    #         amount=AmountWithBreakdown(
    #             currency_code="USD",
    #             value=str(donationItem.unit_amount.value),
    #             breakdown=AmountBreakdown(
    #                 item_total=Money(
    #                     currency_code="USD", value=str(donationItem.unit_amount.value)
    #                 )
    #             )
    #         ),
    #         items=[donationItem]
    #     ))

    logger.debug("---- Begin PayPal Order Creation ----")

    api_response = orders_controller.create_order(
        {
            "body": OrderRequest(
                intent=CheckoutPaymentIntent.CAPTURE, purchase_units=purchase_units
            )
        }
    )
    logger.debug("---- PayPal Order Creation complete ----")
    logger.debug(api_response)
    return api_response


def capture_paypal_payment(
    paypal_order_id: int | str, apis_order: Order
) -> tuple[bool, dict]:
    body = {"id": paypal_order_id, "prefer": "return=representation"}
    logger.debug("---- Begin Capture ----")
    logger.debug(body)

    try:
        api_response: ApiResponse = orders_controller.capture_order(body)
    except ApiException as ex:
        api_response = ex.response

    logger.debug("---- Capture Completed ----")
    logger.debug(api_response)

    apis_order.apiData = api_response.text
    resp_body = json.loads(api_response.text)

    if "payment_source" in resp_body and "card" in resp_body["payment_source"]:
        apis_order.lastFour = api_response.body["payment_source"]["card"]["last_digits"]

    if api_response.is_success():
        apis_order.status = Order.COMPLETED
        apis_order.notes = "PayPal: #" + resp_body["id"][:4]
        apis_order.save()

    elif api_response.is_error():
        logger.debug(resp_body["errors"])
        message = resp_body["errors"]
        logger.debug("---- Transaction Failed ----")
        apis_order.status = Order.FAILED
        apis_order.save()
        return False, {"errors": message}

    logger.debug("---- End Transaction ----")

    return True, api_response.body
