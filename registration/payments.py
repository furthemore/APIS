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

logger = logging.getLogger("django.request")

# Returns two variabies:
#    True/False  - general success flag
#    message - type of failure.
def chargePayment(orderId, ccData, ipAddress):
  try:
    order = Order.objects.get(id=orderId)
    idempotency_key = str(uuid.uuid1())
    convertedTotal = int(order.total*100)

    amount = {'amount': convertedTotal, 'currency': settings.SQUARE_CURRENCY}

    billing_address = {'address_line_1': ccData["address1"], 'address_line_2': ccData["address2"],
                       'locality': ccData["city"], 'administrative_district_level_1': ccData["state"],
                       'postal_code': ccData["postal"], 'country': ccData["country"],
                       'buyer_email_address': ccData["email"],
                       'first_name': ccData["cc_firstname"], 'last_name': ccData["cc_lastname"]}

    body = {'idempotency_key': idempotency_key, 'card_nonce': ccData["nonce"], 'amount_money': amount,
            'reference_id': order.reference, 'billing_address': billing_address}

    print("---- Begin Transaction ----")
    print(body)

    api_instance = TransactionsApi()
    api_response = api_instance.charge(settings.SQUARE_LOCATION_ID, body)

    print("---- Charge Submitted ----")
    print(api_response)

    if api_response.errors and len(api_response.errors) > 0:
        message = api_response.errors[0].details
        print("---- Transaction Failed ----")
        return False, message

    print("---- End Transaction ----")

    return True, ""
  except ApiException as e:
    print("---- Transaction Failed ----")
    print e
    print("---- End Transaction ----")
    logger.exception("!!Failed Square Transaction!!")
    return False, "An unexpected error has occurred."



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
