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
    event = Event.objects.first()
    tz = timezone.get_current_timezone()
    today = tz.localize(datetime.now())
    context = {}
    if event.attendeeRegStart <= today <= event.attendeeRegEnd:
        return render(request, 'registration/registration-form.html', context)
    return render(request, 'registration/closed.html', context)

def flush(request):
    request.session.flush()
    return JsonResponse({'success': True})

###################################
# Jersey Only

def getJersey(request, guid):
    context = {'token': guid}
    return render(request, 'registration/jersey-locate.html', context)

def doneJersey(request):
    context = {}
    return render(request, 'registration/jersey-done.html', context)

def lookupJersey(request):
  try:
    postData = json.loads(request.body)
    email = postData['email']
    token = postData['token']

    attendee = Attendee.objects.filter(email=email, registrationToken=token)
    if attendee.count() == 0:     
        return JsonResponse({'success': False})

    request.session['attendee_id'] = attendee.first().id
    return JsonResponse({'success': True, 'message':'ATTENDEE'})
  except Exception as e:
    return HttpResponseServerError(str(e))

def addJersey(request):
    context = {'attendee': None}
    try:
      attId = request.session['attendee_id']
    except Exception as e:
      return render(request, 'registration/jersey-add.html', context)

    attendee = Attendee.objects.get(id=attId)
    if attendee:
      level = attendee.effectiveLevel()
      option = level.priceleveloption_set.get(optionExtraType='Jersey')
      context = {'attendee': attendee, 'optionid': option.id}
    return render(request, 'registration/jersey-add.html', context)

def checkoutJersey(request):
    postData = json.loads(request.body)
    pbill = postData["billingData"]
    jer = postData['jersey']
    attId = request.session['attendee_id']
    attendee = Attendee.objects.get(id=attId)

    priceLevel = attendee.effectiveLevel()

    orderItem = OrderItem(attendee=attendee, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    jerseySize = ShirtSizes.objects.get(id=int(jer['size']))
    jersey = Jersey(name=jer['name'], number=jer['number'], shirtSize=jerseySize)
    jersey.save()
    jOption = PriceLevelOption.objects.get(id=int(jer['optionId']))
    jerseyOption = AttendeeOptions(option=jOption, orderItem=orderItem, optionValue=jersey.id)
    jerseyOption.save()

    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    order = Order(total=Decimal(80), reference=reference, discount=None,
                  orgDonation=0, charityDonation=0, billingName=pbill['cc_firstname'] + " " + pbill['cc_lastname'],
                  billingAddress1=pbill['address1'], billingAddress2=pbill['address2'],
                  billingCity=pbill['city'], billingState=pbill['state'], billingCountry=pbill['country'],
                  billingPostal=pbill['postal'], billingEmail=pbill['email'])
    order.save()

    orderItem.order = order
    orderItem.save()
    
    result = chargePayment(order.id, pbill)
    try:
      if result:
        sendJerseyEmail(order.id, pbill['email'])
        request.session.flush()
    except Exception as e:
        #none of this should return a failure to the user
        print e

    return JsonResponse({'success': True})
            

###################################
# Staff

def staff(request, guid):
    context = {'token': guid}
    return render(request, 'registration/staff-locate.html', context)

def staffDone(request):
    context = {}
    return render(request, 'registration/staff-done.html', context)

def findStaff(request):
  try:
    postData = json.loads(request.body)
    email = postData['email']
    token = postData['token']

    staff = Staff.objects.get(attendee__email=email, registrationToken=token)
    if not staff:     
      return HttpResponseServerError("No Staff Found")

    request.session['staff_id'] = staff.id
    return JsonResponse({'success': True, 'message':'STAFF'})
  except Exception as e:
    return HttpResponseServerError(str(e))

def infoStaff(request):
    context = {'staff': None}
    try:
      staffId = request.session['staff_id']
    except Exception as e:
      return render(request, 'registration/staff-payment.html', context)

    staff = Staff.objects.get(id=staffId)
    if staff:
	staff_dict = model_to_dict(staff)
        attendee_dict = model_to_dict(staff.attendee)
        if staff.attendee.effectiveLevel():
            lvl_dict = model_to_dict(staff.attendee.effectiveLevel())
        else:
            lvl_dict = {}
        context = {'staff': staff, 'jsonStaff': json.dumps(staff_dict, default=handler), 
                   'jsonAttendee': json.dumps(attendee_dict, default=handler),
                   'jsonLevel': json.dumps(lvl_dict, default=handler)}
    return render(request, 'registration/staff-payment.html', context)

def invoiceStaff(request):
    sessionItems = request.session.get('order_items', [])
    sessionDiscount = request.session.get('discount', "")
    if not sessionItems:
        context = {'orderItems': [], 'total': 0, 'discount': {}}
        request.session.flush()
    else:
        orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
        discount = Discount.objects.get(codeName=sessionDiscount)
        total = getTotal(orderItems, discount)
        context = {'orderItems': orderItems, 'total': total, 'discount': discount}
    return render(request, 'registration/staff-checkout.html', context)


def addStaff(request):
    postData = json.loads(request.body)
    #create attendee from request post
    pda = postData['attendee']
    pdp = postData['priceLevel']
    jer = postData['jersey']
    sjer = postData['staffjersey']
    pds = postData['staff']

    #TODO: get correct event
    event = Event.objects.first()

    attendee = Attendee.objects.get(id=pda['id'])
    if not attendee:
        return JsonResponse({'success': False, 'message': 'Attendee not found'})

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
    attendee.emailsOk=True

    try:
        attendee.save()
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Attendee not saved: ' + e})

    staff = Staff.objects.get(id=pds['id'])
    if 'staff_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Staff record not found'})

    ## Update Staff info
    if not staff:
        return JsonResponse({'success': False, 'message': 'Staff record not found'})

    dept = Department.objects.get(id=pds['department'])
    shirt = ShirtSizes.objects.get(id=pds['shirtsize'])    
    staff.department = dept
    staff.title = pds['title']
    staff.twitter = pds['twitter']
    staff.telegram = pds['telegram']
    staff.shirtsize = shirt
    staff.specialSkills = pds['specialSkills']
    staff.specialFood = pds['specialFood']
    staff.specialMedical = pds['specialMedical']
    staff.contactName = pds['contactName']
    staff.contactPhone = pds['contactPhone']
    staff.contactRelation = pds['contactRelation']

    try:
        staff.save()
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Staff not saved: ' + e})

    priceLevel = PriceLevel.objects.get(id=int(pdp['id']))

    orderItem = OrderItem(attendee=attendee, priceLevel=priceLevel, enteredBy="WEB")
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
    if sjer:
        sjerseySize = ShirtSizes.objects.get(id=int(jer['size']))
        sjersey = StaffJersey(name=sjer['name'], number=sjer['number'], shirtSize=sjerseySize)
        sjersey.save()
        sjOption = PriceLevelOption.objects.get(id=int(sjer['optionId']))
        sjerseyOption = AttendeeOptions(option=sjOption, orderItem=orderItem, optionValue=sjersey.id)
        sjerseyOption.save()

    #add to session order
    orderItems = request.session.get('order_items', [])
    orderItems.append(orderItem.id)
    request.session['order_items'] = orderItems
    request.session["discount"] = "StaffDiscount"

    return JsonResponse({'success': True})


def checkoutStaff(request):
    sessionItems = request.session.get('order_items', [])
    pdisc = request.session.get('discount', "")
    orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
    postData = json.loads(request.body)
    event = Event.objects.first()
   
    #todo: event = Event.objects.get(id=int(postData["eventId"]))

    discount = Discount.objects.get(codeName="StaffDiscount")
    subtotal = getTotal(orderItems, discount)

    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    email = ''
    total = 0
    if subtotal == 0:
      att = orderItems[0].attendee
      order = Order(total=0, reference=reference, discount=discount,
                  orgDonation=0, charityDonation=0, billingName=att.firstName + " " + att.lastName,
                  billingAddress1=att.address1, billingAddress2=att.address2,
                  billingCity=att.city, billingState=att.state, billingCountry=att.country,
                  billingPostal=att.postalCode, billingEmail=att.email, status="Complete")
      order.save()
      email = att.email

      for oitem in orderItems:
          oitem.order = order
          oitem.save()

      sendStaffRegistrationEmail(order.id, email)
      discount.used = discount.used + 1
      discount.save()
      request.session.flush()
      return JsonResponse({'success': True})



    pbill = postData["billingData"]
    porg = Decimal(postData["orgDonation"].strip() or 0.00)
    pcharity = Decimal(postData["charityDonation"].strip() or 0.00)
    if porg < 0: 
      porg = 0
    if pcharity < 0:
      pcharity = 0 

    total = subtotal + porg + pcharity

    order = Order(total=Decimal(total), reference=reference, discount=discount,
                  orgDonation=porg, charityDonation=pcharity, billingName=pbill['cc_firstname'] + " " + pbill['cc_lastname'],
                  billingAddress1=pbill['address1'], billingAddress2=pbill['address2'],
                  billingCity=pbill['city'], billingState=pbill['state'], billingCountry=pbill['country'],
                  billingPostal=pbill['postal'], billingEmail=pbill['email'])
    order.save()
    email = order.billingEmail

    response = chargePayment(order.id, pbill)

    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages') == True:
                sendStaffRegistrationEmail(order.id, email)
                for oitem in orderItems:
                    oitem.order = order
                    oitem.save()
                request.session.flush()
                discount.used = discount.used + 1
                discount.save()
                return JsonResponse({'success': True})
            else:
                if hasattr(response.transactionResponse, 'errors') == True:
                    return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
        else:
            if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
                return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
            else:
                return JsonResponse({'success': False, 'message': str(response.messages.message[0]['text'])})
    else:
        return JsonResponse({'success': False, 'message': "Unknown Error"})

    request.session.flush()
    return JsonResponse({'success': True})



###################################
# Dealers

def dealers(request, guid):
    context = {'token': guid}
    return render(request, 'registration/dealer-locate.html', context)

def newDealer(request):
    event = Event.objects.first()
    tz = timezone.get_current_timezone()
    today = tz.localize(datetime.now())
    context = {}
    if event.dealerRegStart <= today <= event.dealerRegEnd:
        return render(request, 'registration/dealer-form.html', context)
    return render(request, 'registration/dealer-closed.html', context)

def infoDealer(request):
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
        if dealer.attendee.effectiveLevel():
            lvl_dict = model_to_dict(dealer.attendee.effectiveLevel())
        else:
            lvl_dict = {}
        context = {'dealer': dealer, 'jsonDealer': json.dumps(dealer_dict, default=handler), 
                   'jsonTable': json.dumps(table_dict, default=handler),
                   'jsonAttendee': json.dumps(attendee_dict, default=handler),
                   'jsonLevel': json.dumps(lvl_dict, default=handler)}
    return render(request, 'registration/dealer-payment.html', context)

def getDealerTotal(orderItems, discount, dealer):
    subTotal = getTotal(orderItems, discount)
    alreadyPaid = dealer.paidTotal()
    partnerCount = dealer.getPartnerCount()
    total = subTotal + 40*partnerCount + dealer.tableSize.basePrice - dealer.discount - alreadyPaid
    if total < 0: 
      return 0
    return total

def invoiceDealer(request):
    sessionItems = request.session.get('order_items', [])
    sessionDiscount = request.session.get('discount', "")
    if not sessionItems:
        context = {'orderItems': [], 'total': 0, 'discount': {}}
        request.session.flush()
    else:
        dealerId = request.session.get('dealer_id', -1)
        if dealerId == -1: 
            context = {'orderItems': [], 'total': 0, 'discount': {}}
            request.session.flush()
        else:
            dealer = Dealer.objects.get(id=dealerId)
            orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
            discount = Discount.objects.get(codeName=sessionDiscount)
            total = getDealerTotal(orderItems, discount, dealer)
            context = {'orderItems': orderItems, 'total': total, 'discount': discount, 'dealer': dealer}
    return render(request, 'registration/dealer-checkout.html', context)

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

def addDealer(request):
    postData = json.loads(request.body)
    pda = postData['attendee']
    pdd = postData['dealer']
    pdp = postData['priceLevel']
    jer = postData['jersey']

    if 'dealer_id' not in request.session:
        return HttpResponseServerError("Session expired")

    dealer = Dealer.objects.get(id=pdd['id'])
    
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

    #Todo: get price level from post
    priceLevel = PriceLevel.objects.get(id=int(pdp['id']))

    orderItem = OrderItem(attendee=attendee, priceLevel=priceLevel, enteredBy="WEB")
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


    orderItems = request.session.get('order_items', [])
    orderItems.append(orderItem.id)
    request.session['order_items'] = orderItems
    request.session["discount"] = "DealerDiscount"

    return JsonResponse({'success': True})


def checkoutDealer(request):
  try:
    sessionItems = request.session.get('order_items', [])
    pdisc = request.session.get('discount', "")
    orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
    orderItem = orderItems[0]
    if 'dealer_id' not in request.session:
        return HttpResponseServerError("Session expired")

    dealer = Dealer.objects.get(id=request.session.get('dealer_id'))
    postData = json.loads(request.body)
    event = Event.objects.first()

    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    discount = Discount.objects.get(codeName=pdisc)
    subtotal = getDealerTotal(orderItems, discount, dealer)

    if subtotal == 0:
        att = dealer.attendee
        order = Order(total=0, reference=reference, discount=discount,
                  orgDonation=0, charityDonation=0,
                  billingName=att.firstName + " " + att.lastName,
                  billingAddress1=att.address1, billingAddress2=att.address2,
                  billingCity=att.city, billingState=att.state, billingCountry=att.country,
                  billingPostal=att.postalCode, status="Complete")
        order.save()

        orderItem.order = order
        orderItem.save()
        sendDealerPaymentEmail(dealer, order)
        request.session.flush()
        return JsonResponse({'success': True})
      
    porg = Decimal(postData["orgDonation"].strip() or 0.00)
    pcharity = Decimal(postData["charityDonation"].strip() or 0.00)
    if porg < 0: 
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity

    pbill = postData['billingData']
    order = Order(total=Decimal(total), reference=reference, discount=discount,
                  orgDonation=porg, charityDonation=pcharity,
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
                request.session.flush()
                sendDealerPaymentEmail(dealer, order)
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

def addNewDealer(request):
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
    dealer = Dealer(attendee=attendee, businessName=pdd['businessName'], 
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
    discount = request.session.get('discount', "")
    if not sessionItems:
        context = {'orderItems': [], 'total': 0, 'discount': {}}
        request.session.flush()
    else:
        orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
        if discount:
	    discount = Discount.objects.filter(codeName=discount)
            if discount.count() > 0: discount = discount.first()
        total = getTotal(orderItems, discount)
        context = {'orderItems': orderItems, 'total': total, 'discount': discount}
    return render(request, 'registration/checkout.html', context)

def applyDiscount(request):
    dis = request.session.get('discount', "")
    if dis: 
      return JsonResponse({'success': False, 'message': 'Only one discount is allowed per order.'})

    postData = json.loads(request.body)
    #create attendee from request post
    dis = postData['discount']
    
    discount = Discount.objects.filter(codeName=dis)
    if discount.count() == 0:
      return JsonResponse({'success': False, 'message': 'That discount is not valid.'})
    discount = discount.first()
    if not discount.isValid():
      return JsonResponse({'success': False, 'message': 'That discount is not valid.'})
    
    request.session["discount"] = discount.codeName
    return JsonResponse({'success': True})
    


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

    orderItem = OrderItem(attendee=attendee, priceLevel=priceLevel, enteredBy="WEB")
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
        if str(item) == str(id):
            deleteOrderItem(item) 
            order.remove(item)
    request.session['order_items'] = order
    return JsonResponse({'success': True})

def cancelOrder(request):
    #remove order from session
    order = request.session.get('order_items', [])
    for item in order:
        deleteOrderItem(item)
    request.session.flush()
    return JsonResponse({'success': True})

def checkout(request):
    sessionItems = request.session.get('order_items', [])
    pdisc = request.session.get('discount', "")
    orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
    postData = json.loads(request.body)
    porg = Decimal(postData["orgDonation"].strip() or 0.00)
    pcharity = Decimal(postData["charityDonation"].strip() or 0.00)
    pbill = postData["billingData"]
    event = Event.objects.first()
   
    #todo: event = Event.objects.get(id=int(postData["eventId"]))

    discount = Discount.objects.filter(codeName=pdisc)
    if discount.count() > 0 and discount.first().isValid():
        subtotal = getTotal(orderItems, discount.first())
        discount = discount.first()
    else: 
        discount = None
        subtotal = getTotal(orderItems)

    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    if subtotal == 0:
        att = orderItems[0].attendee
        order = Order(total=0, reference=reference, discount=discount,
                  orgDonation=0, charityDonation=0, billingName=att.firstName + " " + att.lastName,
                  billingAddress1=att.address1, billingAddress2=att.address2,
                  billingCity=att.city, billingState=att.state, billingCountry=att.country,
                  billingPostal=att.postalCode, status="Complete", billingEmail=att.email)
        order.save()
        for oitem in orderItems:
            oitem.order = order
            oitem.save()
        del request.session['order_items']
        sendRegistrationEmail(order.id, att.email)
        return JsonResponse({'success': True})

    if porg < 0: 
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity

    order = Order(total=Decimal(total), reference=reference, discount=discount,
                  orgDonation=porg, charityDonation=pcharity, billingName=pbill['cc_firstname'] + " " + pbill['cc_lastname'],
                  billingAddress1=pbill['address1'], billingAddress2=pbill['address2'],
                  billingCity=pbill['city'], billingState=pbill['state'], billingCountry=pbill['country'],
                  billingPostal=pbill['postal'], billingEmail=pbill['email'])
    order.save()

    
    response = chargePayment(order.id, pbill)

    if response is not None:
          if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages') == True:
                request.session.flush()
                for oitem in orderItems:
                    oitem.order = order
                    oitem.save()
                sendRegistrationEmail(order.id, pbill['email'])
                if discount:
                    discount.used = discount.used + 1
                    discount.save()
                return JsonResponse({'success': True})
            else:
                if hasattr(response.transactionResponse, 'errors') == True:
                    return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
          else:
            if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
                return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
            else:
                return JsonResponse({'success': False, 'message': str(response.messages.message[0]['text'])})
    else:
          return JsonResponse({'success': False, 'message': "Unknown Error"})


    request.session.flush()
    return JsonResponse({'success': True})

def cartDone(request):
    context = {}
    return render(request, 'registration/done.html', context)



###################################
# Utilities

def getEvents(request):
    events = Event.objects.all()
    data = [{'name': ev.name, 'id': ev.id, 'dealerStart': ev.dealerRegStart, 'dealerEnd': ev.dealerRegEnd, 'staffStart': ev.staffRegStart, 'staffEnd': ev.staffRegEnd, 'attendeeStart': ev.attendeeRegStart, 'attendeeEnd': ev.attendeeRegEnd} for ev in events]
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def getDepartments(request):
    depts = Department.objects.filter(volunteerListOk=True).order_by('name')
    data = [{'name': item.name, 'id': item.id} for item in depts]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getAllDepartments(request):
    depts = Department.objects.order_by('name')
    data = [{'name': item.name, 'id': item.id} for item in depts]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getPriceLevels(request):
    dealer = request.session.get('dealer_id', -1)
    staff = request.session.get('staff_id', -1)
    #hide any irrelevant price levels if something in session
    att = None
    if dealer > 0: 
        att = Dealer.objects.get(id=dealer).attendee
    if staff > 0:
        att = Staff.objects.get(id=staff).attendee
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=True, startDate__lte=now, endDate__gte=now)
    if att and att.effectiveLevel():
        levels = levels.exclude(basePrice__lt=att.effectiveLevel().basePrice)
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

def getJerseyNumbers(request):
    jerseys = Jersey.objects.all()
    data = [str(jersey.number) for jersey in jerseys]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getStaffJerseyNumbers(request):
    jerseys = StaffJersey.objects.all()
    data = [str(jersey.number) for jersey in jerseys]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getSessionAddresses(request):
    sessionItems = request.session.get('order_items', [])
    if not sessionItems:
        data = {}
    else:
        orderItems = OrderItem.objects.filter(id__in=sessionItems)
        data = [{'id': oi.attendee.id, 'fname': oi.attendee.firstName, 'lname': oi.attendee.lastName, 'email': oi.attendee.email, 'address1': oi.attendee.address1, 'address2': oi.attendee.address2, 'city': oi.attendee.city, 'state': oi.attendee.state, 'country': oi.attendee.country, 'postalCode': oi.attendee.postalCode} for oi in orderItems]
        context = {'addresses': data}
    return HttpResponse(json.dumps(data), content_type='application/json')    


##################################
# Not Endpoints

def getConfirmationToken():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase+string.digits) for _ in range(6))

def deleteOrderItem(id):
    orderItems = OrderItem.objects.filter(id=id)
    if orderItems.count() == 0: 
      return
    orderItem = orderItems.first()
    #Delete any jerseys. Other options will cascade delete properly.
    jerseyOptions = AttendeeOptions.objects.filter(orderItem__attendee=orderItem.attendee, option__optionExtraType='Jersey')
    for jerOpt in jerseyOptions:
      jersey = Jersey.objects.get(id=jerOpt.optionValue)
      jersey.delete()
    orderItem.attendee.delete()
    orderItem.delete()

def getTotal(orderItems, disc = ""):
    total = 0
    if not orderItems: return total
    for item in orderItems:
        itemSubTotal = item.priceLevel.basePrice
        effLevel = item.attendee.effectiveLevel()
        if effLevel:
            itemTotal = itemSubTotal - effLevel.basePrice
        else: 
            itemTotal = itemSubTotal

        for option in item.attendeeoptions_set.all():
            if option.option.optionExtraType == 'int':
                itemTotal += (option.option.optionPrice*Decimal(option.optionValue))
            else:
                itemTotal += option.option.optionPrice

        if disc:
            discount = Discount.objects.get(codeName=disc)
            if discount.isValid():
              if discount.amountOff:
                itemTotal -= discount.amountOff
              elif discount.percentOff:
                itemTotal -= Decimal(float(itemTotal) * float(discount.percentOff)/100)

        if itemTotal > 0:
            total += itemTotal
    return total


def handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return str(obj)
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))
