from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseServerError, JsonResponse
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from datetime import datetime
from decimal import *
import json
import random
import string

from .emails import *
from .models import *
from .payments import chargePayment

# Create your views here.

def index(request):
    context = {}
    return render(request, 'registration/registration-form.html', context)

def staff(request, guid):
    pass


###################################
# Dealers

def dealers(request, guid):
    context = {'token': guid}
    return render(request, 'registration/dealer-locate.html', context)

def newDealer(request):
    context = {}
    return render(request, 'registration/dealer-form.html', context)

def invoiceDealer(request):
    context = {'dealer': None}
    try:
      dealerId = request.session['dealer_id']
    except Exception as e:
      return render(request, 'registration/dealer-payment.html', context)

    dealer = Dealer.objects.get(id=dealerId)
    if dealer:
	dealer_dict = model_to_dict(dealer)
        attendee_dict = model_to_dict(dealer.attendee)
        table_dict = model_to_dict(dealer.tableSize)
        context = {'dealer': dealer, 'jsonDealer': json.dumps(dealer_dict, default=handler), 
                   'jsonAttendee': json.dumps(attendee_dict, default=handler), 
                   'jsonTable': json.dumps(table_dict, default=handler)}
    return render(request, 'registration/dealer-payment.html', context)

def thanksDealer(request):
    context = {}
    return render(request, 'registration/dealer-thanks.html', context)

def updateDealer(request):
    context = {}
    return render(request, 'registration/dealer-update.html', context)

def doneDealer(request):
    context = {}
    return render(request, 'registration/dealer-done.html', context)

def findDealer(request):
  try:
    postData = json.loads(request.body)
    email = postData['email']
    token = postData['token']

    dealer = Dealer.objects.get(attendee__email=email, registrationToken=token)
    if not dealer:     
      return HttpResponseServerError("No Dealer Found")

    request.session['dealer_id'] = dealer.id
    return JsonResponse({'success': True, 'message':'DEALER'})
  except Exception as e:
    return HttpResponseServerError(str(e))

def checkoutDealer(request):
  try:
    postData = json.loads(request.body)
    pda = postData['attendee']
    pdd = postData['dealer']

    dealer = Dealer.objects.get(id=pdd['id'])
    
    if 'dealer_id' not in request.session:
        return HttpResponseServerError("Session expired")

    ## Update Dealer info
    if not dealer:
        return HttpResponseServerError("Dealer id not found")
    
    dealer.businessName=pdd['businessName'] 
    dealer.website=pdd['website'] 
    dealer.description=pdd['description'] 
    dealer.license=pdd['license']    
    dealer.needPower=pdd['power']
    dealer.needWifi=pdd['wifi']
    dealer.wallSpace=pdd['wall']
    dealer.nearTo=pdd['near'] 
    dealer.farFrom=pdd['far']
    dealer.reception=pdd['reception']
    dealer.artShow=pdd['artShow']
    dealer.charityRaffle=pdd['charityRaffle'] 
    dealer.breakfast=pdd['breakfast']
    dealer.willSwitch=pdd['switch']  
    dealer.buttonOffer=pdd['buttonOffer']

    try:
        dealer.save()
    except Exception as e:
        return HttpResponseServerError(str(e))

    ## Update Attendee info
    attendee = Attendee.objects.get(id=pda['id'])
    if not attendee:
        return HttpResponseServerError("Attendee id not found")

    attendee.firstName=pda['firstName']
    attendee.lastName=pda['lastName']
    attendee.address1=pda['address1']
    attendee.address2=pda['address2']
    attendee.city=pda['city']
    attendee.state=pda['state']
    attendee.country=pda['country']
    attendee.postalCode=pda['postal']
    attendee.phone=pda['phone']
    attendee.badgeName=pda['badgeName']

    try:
        attendee.save()
    except Exception as e:
        return HttpResponseServerError(str(e))

    if dealer.paid():
        sendDealerUpdateEmail(dealer.id)
        return JsonResponse({'success': True})

    pbill = postData['billingData']

    basePrice = dealer.tableSize.basePrice
    partners = dealer.partners.split(', ')
    partnerCount = 0
    for part in partners:
        if part.find("name") > -1 and part.split(':')[1] != "":
            partnerCount = partnerCount + 1

    total = 40*partnerCount + basePrice - dealer.discount

    priceLevel = PriceLevel.objects.get(name='Dealer')

    ccode = getConfirmationCode()
    while OrderItem.objects.filter(confirmationCode=ccode).count() > 0:
        ccode = getConfirmationCode()

    orderItem = OrderItem(attendee=attendee, priceLevel=priceLevel, enteredBy="WEB", confirmationCode=ccode)
    orderItem.save()

    reference = getConfirmationCode()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationCode()

    if total == 0:
        order = Order(total=0, reference=reference,
                  billingName=pda['firstName'] + " " + pda['lastName'],
                  billingAddress1=pda['address1'], billingAddress2=pda['address2'],
                  billingCity=pda['city'], billingState=pda['state'], billingCountry=pda['country'],
                  billingPostal=pda['postal'], status="Complete")
        order.save()

        orderItem.order = order
        orderItem.save()
        sendDealerPaymentEmail(dealer.id, reference)
        return JsonResponse({'success': True})
      

    order = Order(total=Decimal(total), reference=reference,
                  billingName=pbill['cc_firstname'] + " " + pbill['cc_lastname'],
                  billingAddress1=pbill['address1'], billingAddress2=pbill['address2'],
                  billingCity=pbill['city'], billingState=pbill['state'], billingCountry=pbill['country'],
                  billingPostal=pbill['postal'])
    order.save()

    orderItem.order = order
    orderItem.save()
    

    response = chargePayment(order.id, pbill)

    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages') == True:
                del request.session['dealer_id']
                sendDealerPaymentEmail(dealer.id, reference)
                return JsonResponse({'success': True})
            else:
                if hasattr(response.transactionResponse, 'errors') == True:
                    order.delete()
                    orderItem.delete()
                    return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
        else:
            if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
                order.delete()
                orderItem.delete()
                return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
            else:
                order.delete()
                orderItem.delete()
                return JsonResponse({'success': False, 'message': str(response.messages.message[0]['text'])})
    else:
        order.delete()
        orderItem.delete()
        return JsonResponse({'success': False, 'message': "Unknown Error"})
        
  except Exception as e:
    return HttpResponseServerError(str(e))

def addDealer(request):
  try:
    postData = json.loads(request.body)
    #create attendee from request post
    pda = postData['attendee']
    pdd = postData['dealer']

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda['birthdate'], '%m/%d/%Y' ))
    #TODO: get correct event
    event = Event.objects.first()

    attendee = Attendee(firstName=pda['firstName'], lastName=pda['lastName'], address1=pda['address1'], address2=pda['address2'],
                        city=pda['city'], state=pda['state'], country=pda['country'], postalCode=pda['postal'],
                        phone=pda['phone'], email=pda['email'], birthdate=birthdate,
                        emailsOk=pda['emailsOk'], event=event )
    attendee.save()

    tablesize = TableSize.objects.get(id=pdd['tableSize'])
    dealer = Dealer(attendee=attendee, registrationToken=getRegistrationToken(), businessName=pdd['businessName'], 
                    website=pdd['website'], description=pdd['description'], license=pdd['license'], needPower=pdd['power'],
                    needWifi=pdd['wifi'], wallSpace=pdd['wall'], nearTo=pdd['near'], farFrom=pdd['far'], tableSize=tablesize,
                    chairs=pdd['chairs'], reception=pdd['reception'], artShow=pdd['artShow'], charityRaffle=pdd['charityRaffle'], 
                    breakfast=pdd['breakfast'], willSwitch=pdd['switch'], tables=pdd['tables'], 
                    agreeToRules=pdd['agreeToRules'], partners=pdd['partners'], buttonOffer=pdd['buttonOffer'])
    dealer.save()
    sendDealerApplicationEmail(dealer.id)    
    return JsonResponse({'success': True})
  except Exception as e:
    return HttpResponseServerError(str(e))


###################################
# Attendees

def getCart(request):
    sessionItems = request.session.get('order_items', [])
    if not sessionItems:
        context = {'orderItems': [], 'total': 0}
    else:
        orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
        total = getTotal(orderItems)
        context = {'orderItems': orderItems, 'total': total}
    return render(request, 'registration/checkout.html', context)

def getCartAddresses(request):
    sessionItems = request.session.get('order_items', [])
    if not sessionItems:
        data = {}
    else:
        orderItems = OrderItem.objects.filter(id__in=sessionItems)
        for oi in orderItems: 
            pass
        context = {'orderItems': orderItems, 'total': total}
    return HttpResponse(json.dumps(data), content_type='application/json')
    

def addToCart(request):
    postData = json.loads(request.body)
    #create attendee from request post
    pda = postData['attendee']
    pdp = postData['priceLevel']
    jer = postData['jersey']

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda['birthdate'], '%m/%d/%Y' ))
    #TODO: get correct event
    event = Event.objects.first()

    attendee = Attendee(firstName=pda['firstName'], lastName=pda['lastName'], address1=pda['address1'], address2=pda['address2'],
                        city=pda['city'], state=pda['state'], country=pda['country'], postalCode=pda['postal'],
                        phone=pda['phone'], email=pda['email'], birthdate=birthdate,
                        badgeName=pda['badgeName'], emailsOk=pda['emailsOk'], volunteerContact=len(pda['volDepts']) > 0, volunteerDepts=pda['volDepts'],
                        event=event )
    attendee.save()

    priceLevel = PriceLevel.objects.get(id=int(pdp['id']))

    ccode = getConfirmationCode()
    while OrderItem.objects.filter(confirmationCode=ccode).count() > 0:
        ccode = getConfirmationCode()
    orderItem = OrderItem(attendee=attendee, priceLevel=priceLevel, enteredBy="WEB", confirmationCode=ccode)
    orderItem.save()

    for option in pdp['options']:
        plOption = PriceLevelOption.objects.get(id=int(option['id']))
        attendeeOption = AttendeeOptions(option=plOption, orderItem=orderItem, optionValue=option['value'])
        attendeeOption.save()

    if jer:
        jerseySize = ShirtSizes.objects.get(id=int(jer['size']))
        jersey = Jersey(name=jer['name'], number=jer['number'], shirtSize=jerseySize)
        jersey.save()
        jOption = PriceLevelOption.objects.get(id=int(jer['optionId']))
        jerseyOption = AttendeeOptions(option=jOption, orderItem=orderItem, optionValue=jersey.id)
        jerseyOption.save()

    #add attendee to session order
    orderItems = request.session.get('order_items', [])
    orderItems.append(orderItem.id)
    request.session['order_items'] = orderItems
    return JsonResponse({'success': True})


def removeFromCart(request):
    #locate attendee in session order
    order = request.session.get('order_items', [])
    postData = json.loads(request.body)
    id = postData['id']
    #remove attendee from session order
    for item in order:
        if item == id:
            deleteOrderItem(id) 
            order.remove(item)
    request.session['order_items'] = order
    return HttpResponse("Success")    

def cancelOrder(request):
    #remove order from session
    order = request.session.get('order_items', [])
    for item in order:
        deleteOrderItem(item)
    request.session['order_items'] = []
    return HttpResponse("Order Cancelled")

def checkout(request):
    sessionItems = request.session.get('order_items', [])
    orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
    postData = json.loads(request.body)
    pdisc = postData["discount"].strip()
    porg = Decimal(postData["orgDonation"].strip() or 0.00)
    pcharity = Decimal(postData["charityDonation"].strip() or 0.00)
    pbill = postData["billingData"]
    event = Event.objects.get(id=int(postData["eventId"]))

    if porg < 0: 
        porg = 0
    if pcharity < 0:
        pcharity = 0
    discount = Discount.objects.get(codeName=pdisc)
    if discount and discount.isValid():
        subtotal = getTotal(orderItems, discount)
    else: 
        discount = None
        subtotal = getTotal(orderItems)
    total = subtotal + porg + pcharity

    reference = getConfirmationCode()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationCode()

    order = Order(total=Decimal(total), reference=reference, discount=discount,
                  orgDonation=porg, charityDonation=pcharity, billingName=pbill['cc_name'],
                  billingAddress1=pbill['address1'], billingAddress2=pbill['address2'],
                  billingCity=pbill['city'], billingState=pbill['state'], billingCountry=pbill['country'],
                  billingPostal=pbill['postal'], billingEmail=pbill['email'])
    order.save()

    for oitem in orderItems:
        oitem.order = order
        oitem.save()
    
    result = chargePayment(order.id, pbill)
    #TODO: redirect properly
    if result:
        #TODO: send success email
        return HttpResponse(result)    
    else:
        return HttpResponse("Failure")    



###################################
# Utilities

def getDepartments(request):
    depts = Department.objects.filter(volunteerListOk=True).order_by('name')
    data = [{'name': item.name, 'id': item.id} for item in depts]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getPriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=True, startDate__lte=now, endDate__gte=now)
    data = [{'name': level.name, 'id':level.id,  'base_price': level.basePrice.__str__(), 'description': level.description,'options': [{'name': option.optionName, 'value': option.optionPrice, 'id': option.id, 'required': option.required, 'type': option.optionExtraType, "list": option.getList() } for option in level.priceleveloption_set.order_by('optionPrice').all() ]} for level in levels]
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def getShirtSizes(request):
    sizes = ShirtSizes.objects.all()
    data = [{'name': size.name, 'id': size.id} for size in sizes]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getTableSizes(request):
    sizes = TableSize.objects.all()
    data = [{'name': size.name, 'id': size.id, 'description': size.description, 'chairMin': size.chairMin, 'chairMax': size.chairMax, 'tableMin': size.tableMin, 'tableMax': size.tableMax, 'partnerMin': size.partnerMin, 'partnerMax': size.partnerMax, 'basePrice': str(size.basePrice)} for size in sizes]
    return HttpResponse(json.dumps(data), content_type='application/json')


##################################
# Not Endpoints

def getRegistrationToken():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase+string.digits) for _ in range(15))

def getConfirmationCode():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase+string.digits) for _ in range(6))
        
def deleteOrderItem(id):
    orderItem = OrderItem.objects.get(id=id)
    orderItem.attendee.delete()
    orderItem.delete()

def getTotal(orderItems, discount = None):
    total = 0
    if not orderItems: return total
    for item in orderItems:
        itemTotal = item.priceLevel.basePrice
        for option in item.attendeeoptions_set.all():
            itemTotal += option.option.optionPrice
        if discount:
            if discount.amountOff:
                itemTotal -= discount.amountOff
            elif discount.percentOff:
                itemTotal -= Decimal(float(itemTotal) * float(discount.percentOff)/100)
        if itemTotal > 0:
            total += itemTotal
    return total

def cleanupAbandons():
    pass

def handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return str(obj)
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))
