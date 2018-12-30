from django.conf import settings

from decimal import *
import json
import os
import uuid
import logging

from .models import *

import squareconnect
from squareconnect.rest import ApiException
from squareconnect.apis.transactions_api import TransactionsApi
from squareconnect.apis.locations_api import LocationsApi

squareconnect.configuration.access_token = settings.SQUARE_ACCESS_TOKEN
logger = logging.getLogger('registration.payments')

def chargePayment(order, ccData, ipAddress):
    """
    Returns two variabies:
        success - general success flag
        message - type of failure.
    """

    try:
        idempotency_key = str(uuid.uuid1())
        convertedTotal = int(order.total*100)

        amount = {'amount': convertedTotal, 'currency': settings.SQUARE_CURRENCY}

        billing_address = {
            'postal_code' : ccData['card_data']['billing_postal_code'],
        }

        try:
            billing_address.update(
                {'address_line_1': ccData["address1"], 'address_line_2': ccData["address2"],
                 'locality': ccData["city"], 'administrative_district_level_1': ccData["state"],
                 'postal_code': ccData["postal"], 'country': ccData["country"],
                 'buyer_email_address': ccData["email"],
                 'first_name': ccData["cc_firstname"], 'last_name': ccData["cc_lastname"]}
            )
        except KeyError as e:
            logger.debug("One or more billing address field omited - skipping")

        body = {
            'idempotency_key': idempotency_key,
            'card_nonce': ccData["nonce"], 
            'amount_money': amount,
            'reference_id': order.reference,
            'billing_address': billing_address
        }

        logger.debug("---- Begin Transaction ----")
        logger.debug(body)

        api_instance = TransactionsApi()
        api_instance.api_client.configuration.access_token = settings.SQUARE_ACCESS_TOKEN
        api_response = api_instance.charge(settings.SQUARE_LOCATION_ID, body)

        logger.debug("---- Charge Submitted ----")
        logger.debug(api_response)

        #try:
        #import pdb; pdb.set_trace()
        order.lastFour = api_response.transaction.tenders[0].card_details.card.last_4
        order.apiData = json.dumps(api_response.to_dict())
        order.notes = "Square: #" + api_response.transaction.id[:4]
        #except Exception as e:
        #    logger.debug(dir(api_response))
        #    logger.exception(e)
        order.save()

        if api_response.errors and len(api_response.errors) > 0:
            message = api_response.errors[0].details
            logger.debug("---- Transaction Failed ----")
            return False, message

        logger.debug("---- End Transaction ----")

        return True, ""
    except ApiException as e:
        logger.debug("---- Transaction Failed ----")
        logger.error("!!Failed Square Transaction!!")
        logger.exception(e)
        logger.debug("---- End Transaction ----")
        try:
            return False, json.loads(e.body)
        except:
            return False, str(e)


def cardType(number):
    number = str(number)
    cardtype = ""
    if len(number) == 15:
        if number[:2] == "34" or number[:2] == "37":
            cardtype = "American Express"
    if len(number) == 13:
        if number[:1] == "4":
            cardtype = "Visa"
    if len(number) == 16:
        if number[:4] == "6011":
            cardtype = "Discover"
        if int(number[:2]) >= 51 and int(number[:2]) <= 55:
            cardtype = "Master Card"
        if number[:1] == "4":
            cardtype = "Visa"
    return cardtype




#from authorizenet import apicontractsv1
#from authorizenet.apicontrollers import *

def chargePayment_authnet(orderId, ccData, ipAddress):
#    order = Order.objects.get(id=orderId)
#    clientIP = ipAddress

#    merchantAuth = apicontractsv1.merchantAuthenticationType()
#    merchantAuth.name = settings.AUTHNET_NAME
#    merchantAuth.transactionKey = settings.AUTHNET_TRANSACTIONKEY

#    creditCard = apicontractsv1.creditCardType()
#    creditCard.cardNumber = ccData['cc_number']
#    creditCard.expirationDate = ccData['cc_year'] + '-' + ccData['cc_month']
#    billTo = apicontractsv1.customerAddressType()
#    billTo.firstName = ccData['cc_firstname']
#    billTo.lastName = ccData['cc_lastname']
#    billTo.address = ccData['address1'] + " " + ccData['address2']
#    billTo.city = ccData['city']
#    billTo.state = ccData['state']
#    billTo.zip = ccData['postal']
#    billTo.country = ccData['country']

#    ordertype = apicontractsv1.orderType()
#    ordertype.invoiceNumber = order.reference
#    ordertype.description = "APIS"
#    payment = apicontractsv1.paymentType()
#    payment.creditCard = creditCard
#    transactionrequest = apicontractsv1.transactionRequestType()
#    transactionrequest.transactionType ="authCaptureTransaction"
#    transactionrequest.amount = order.total
#    transactionrequest.payment = payment
#    transactionrequest.billTo = billTo
#    transactionrequest.order = ordertype
#    transactionrequest.customerIP = clientIP
#    createtransactionrequest = apicontractsv1.createTransactionRequest()
#    createtransactionrequest.merchantAuthentication = merchantAuth
#    createtransactionrequest.refId = order.reference

#    createtransactionrequest.transactionRequest = transactionrequest
#    createtransactioncontroller = createTransactionController(createtransactionrequest)
#    createtransactioncontroller.execute()
#    response = createtransactioncontroller.getresponse()
#    if response is not None:
#        if response.messages.resultCode == "Ok":
#            if hasattr(response.transactionResponse, 'messages') == True:
#                print ('Successfully created transaction with Transaction ID: %s' % response.transactionResponse.transId);
#                print ('Transaction Response Code: %s' % response.transactionResponse.responseCode);
#                print ('Message Code: %s' % response.transactionResponse.messages.message[0].code);
#                print ('Description: %s' % response.transactionResponse.messages.message[0].description);
#            else:
#                print ('Failed Transaction.');
#                if hasattr(response.transactionResponse, 'errors') == True:
#                    print ('Error Code:  %s' % str(response.transactionResponse.errors.error[0].errorCode));
#                    print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText);
#        else:
#            print ('Failed Transaction.');
#            if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
#                print ('Error Code: %s' % str(response.transactionResponse.errors.error[0].errorCode));
#                print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText);
#            else:
#                print ('Error Code: %s' % response.messages.message[0]['code'].text);
#                print ('Error message: %s' % response.messages.message[0]['text'].text);
#    else:
#        print ('Null Response.');

#    return response
    return None

# vim: ts=4 sts=4 sw=4 expandtab smartindent
