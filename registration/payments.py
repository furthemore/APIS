from django.conf import settings
#from authorizenet import apicontractsv1
#from authorizenet.apicontrollers import *
from decimal import *

import payeezy
import json

import os

from .models import *

#-- sandbox credentials --

payeezy.apikey = "dwuKS5zAtWxj4FuRyVAE56iezJC9iMUI"
payeezy.apisecret = "3401375f1dac9b3fe261ddd99fc984a6cf46c812458246914bec429b80f81bc6"
payeezy.token = "fdoa-f8b39d0df4ae3e58384aa202919b4a8cf8b39d0df4ae3e58"   #Merchant token, not account token

#-- sandbox environment --

payeezy.url = "https://api-cert.payeezy.com/v1/transactions"
payeezy.tokenurl = "https://api-cert.payeezy.com/v1/securitytokens"

#-- production environment --
# payeezy.url = "https://api.payeezy.com/v1/transactions"
# payeezy.tokenurl = "https://api.payeezy.com/v1/securitytokens"


# Returns two variabies: 
#    True/False  - general success flag
#    message - type of failure. 
def chargePayment(orderId, ccData, ipAddress):

  try:
    order = Order.objects.get(id=orderId)
    total = int(order.total * 100)

    cardtype = cardType(ccData["cc_number"])
    if cardtype == "":
        return False, "Card Type is not recognized"

    print ("************---------- Authorize Response:Start ---------------*****************" );

    responseAuthorize =  payeezy.transactions.authorize( amount=total,
                                                     currency_code='usd',
                                                     cardholder_name=ccData["cc_firstname"] + " " + ccData["cc_lastname"],
                                                     card_number=ccData["cc_number"],
                                                     card_expiry=str(ccData["cc_month"]) + (ccData["cc_year"][2:]),
                                                     card_cvv=ccData["cc_security"],
                                                     card_type=cardtype,
                                                     description='APIS Payment - ' + order.reference
                                                    );


    print(responseAuthorize);
    print (" ** " + json.dumps(responseAuthorize.json(), indent=3) ); 
    print ("************---------- Authorize Response:End ---------------*****************" );

    status = responseAuthorize.json()['transaction_status']

    if status == "Declined": 
        return False, "Authorization was declined, please check your information and try again."
    if status == "Not Processed": 
        return False, "An unexpected error has occurred."

    transactionTag = responseAuthorize.json()['transaction_tag']
    transactionID = responseAuthorize.json()['transaction_id']

    print("");
    print(" transactionTag from Authorize transactions: " + transactionTag );
    print(" transactionID from Authorize transactions : " + transactionID);
    print(" Now calling Payeezy API: Credit Card Capture ");

    print ("************---------- Capture Response:Start ---------------*****************" );
    responseCapture =  payeezy.transactions.capture(amount=total,
                                                currency_code='usd',
                                                transactionTag=transactionTag,
                                                transactionID=transactionID,
                                                description='APIS Payment - ' + order.reference
    );
    print (" ** " + json.dumps(responseCapture.json(), indent=3) );
    print ("************---------- Capture Response:End ---------------*****************" );

    status = responseCapture.json()['transaction_status']

    if status == "Declined": 
        return False, "Authorization was declined, please check your information and try again."
    if status == "Not Processed": 
        return False, "An unexpected error has occurred."


    return True, ""
  except Exception as e:
    print e
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

def _chargePayment(orderId, ccData, ipAddress):
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
