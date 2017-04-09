from django.conf import settings
from authorizenet import apicontractsv1
from authorizenet.apicontrollers import *
from decimal import *

import os

from .models import *

def chargePayment(orderId, ccData, ipAddress):
    order = Order.objects.get(id=orderId)
    clientIP = ipAddress

    merchantAuth = apicontractsv1.merchantAuthenticationType()
    merchantAuth.name = settings.AUTHNET_NAME
    merchantAuth.transactionKey = settings.AUTHNET_TRANSACTIONKEY

    creditCard = apicontractsv1.creditCardType()
    creditCard.cardNumber = ccData['cc_number']
    creditCard.expirationDate = ccData['cc_year'] + '-' + ccData['cc_month']
 
    billTo = apicontractsv1.customerAddressType()
    billTo.firstName = ccData['cc_firstname']
    billTo.lastName = ccData['cc_lastname']
    billTo.address = ccData['address1'] + " " + ccData['address2']
    billTo.city = ccData['city']
    billTo.state = ccData['state']
    billTo.zip = ccData['postal']
    billTo.country = ccData['country']

    ordertype = apicontractsv1.orderType()
    ordertype.invoiceNumber = order.reference
    ordertype.description = "APIS"
 
    payment = apicontractsv1.paymentType()
    payment.creditCard = creditCard
 
    transactionrequest = apicontractsv1.transactionRequestType()
    transactionrequest.transactionType ="authCaptureTransaction"
    transactionrequest.amount = order.total
    transactionrequest.payment = payment
    transactionrequest.billTo = billTo
    transactionrequest.order = ordertype
    transactionrequest.customerIP = clientIP
 
    createtransactionrequest = apicontractsv1.createTransactionRequest()
    createtransactionrequest.merchantAuthentication = merchantAuth
    createtransactionrequest.refId = order.reference

    createtransactionrequest.transactionRequest = transactionrequest
    createtransactioncontroller = createTransactionController(createtransactionrequest)
    createtransactioncontroller.execute()
 
    response = createtransactioncontroller.getresponse()
    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages') == True:
                print ('Successfully created transaction with Transaction ID: %s' % response.transactionResponse.transId);
                print ('Transaction Response Code: %s' % response.transactionResponse.responseCode);
                print ('Message Code: %s' % response.transactionResponse.messages.message[0].code);
                print ('Description: %s' % response.transactionResponse.messages.message[0].description);
            else:
                print ('Failed Transaction.');
                if hasattr(response.transactionResponse, 'errors') == True:
                    print ('Error Code:  %s' % str(response.transactionResponse.errors.error[0].errorCode));
                    print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText);
        else:
            print ('Failed Transaction.');
            if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
                print ('Error Code: %s' % str(response.transactionResponse.errors.error[0].errorCode));
                print ('Error message: %s' % response.transactionResponse.errors.error[0].errorText);
            else:
                print ('Error Code: %s' % response.messages.message[0]['code'].text);
                print ('Error message: %s' % response.messages.message[0]['text'].text);
    else:
        print ('Null Response.');
    
    return response
 
