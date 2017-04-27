from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseServerError, JsonResponse
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from datetime import datetime
from decimal import *
from operator import itemgetter
import os
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
# Staff Jersey Only

def getStaffJersey(request, guid):
    context = {'token': guid}
    return render(request, 'registration/sjersey-locate.html', context)

def doneStaffJersey(request):
    context = {}
    return render(request, 'registration/sjersey-done.html', context)

def lookupStaffJersey(request):
  try:
    postData = json.loads(request.body)
    email = postData['email']
    token = postData['token']
    staff = Staff.objects.filter(attendee__email__iexact=email, registrationToken=token)
    if staff.count() == 0:     
        return JsonResponse({'success': False})

    request.session['staff_id'] = staff.first().id
    return JsonResponse({'success': True, 'message':'STAFF'})
  except Exception as e:
    return HttpResponseServerError(str(e))

def addStaffJersey(request):
    context = {'attendee': None}
    try:
      staffId = request.session['staff_id']
    except Exception as e:
      return render(request, 'registration/sjersey-add.html', context)

    staff = Staff.objects.get(id=staffId)
    if staff.attendee:
      level = staff.attendee.effectiveLevel()
      option = level.priceleveloption_set.get(optionExtraType='StaffJersey')
      context = {'attendee': staff.attendee, 'optionid': option.id}
    return render(request, 'registration/sjersey-add.html', context)

def checkoutStaffJersey(request):
    postData = json.loads(request.body)
    pbill = postData["billingData"]
    jer = postData['jersey']
    staffId = request.session['staff_id']
    staff = Staff.objects.get(id=staffId)

    priceLevel = staff.attendee.effectiveLevel()

    orderItem = OrderItem(attendee=staff.attendee, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    jerseySize = ShirtSizes.objects.get(id=int(jer['size']))
    jersey = StaffJersey(name=jer['name'], number=jer['number'], shirtSize=jerseySize)
    jersey.save()
    jOption = PriceLevelOption.objects.get(id=int(jer['optionId']))
    jerseyOption = AttendeeOptions(option=jOption, orderItem=orderItem, optionValue=jersey.id)
    jerseyOption.save()

    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    order = Order(total=Decimal(60), reference=reference, discount=None,
                  orgDonation=0, charityDonation=0, billingName=pbill['cc_firstname'] + " " + pbill['cc_lastname'],
                  billingAddress1=pbill['address1'], billingAddress2=pbill['address2'],
                  billingCity=pbill['city'], billingState=pbill['state'], billingCountry=pbill['country'],
                  billingPostal=pbill['postal'], billingEmail=pbill['email'])
    order.save()

    orderItem.order = order
    orderItem.save()
    
    response = chargePayment(order.id, pbill, get_client_ip(request))
    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages') == True:
                sendStaffJerseyEmail(order.id, pbill['email'])
                orderItem.order = order
                orderItem.save()
                request.session.flush()
                return JsonResponse({'success': True})
            else:
                if hasattr(response.transactionResponse, 'errors') == True:
                    order.delete()
                    return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
        else:
            if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
            else:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.messages.message[0]['text'])})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': "Unknown Error"})


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
    attendee = Attendee.objects.filter(email__iexact=email, registrationToken=token)
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
    
    response = chargePayment(order.id, pbill, get_client_ip(request))
    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages') == True:
                sendJerseyEmail(order.id, pbill['email'])
                orderItem.order = order
                orderItem.save()
                request.session.flush()
                return JsonResponse({'success': True})
            else:
                if hasattr(response.transactionResponse, 'errors') == True:
                    order.delete()
                    return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
        else:
            if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
            else:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.messages.message[0]['text'])})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': "Unknown Error"})


    request.session.flush()
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

    staff = Staff.objects.get(attendee__email__iexact=email, registrationToken=token)
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
        staffId = request.session['staff_id']
        staff = Staff.objects.get(id=staffId)
        orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
        discount = Discount.objects.get(codeName=sessionDiscount)
        total = getStaffTotal(orderItems, discount, staff)
        context = {'orderItems': orderItems, 'total': total, 'discount': discount, 'staff': staff}
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
        sjerseySize = ShirtSizes.objects.get(id=int(sjer['size']))
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


def getStaffTotal(orderItems, discount, staff):
    if staff.attendee.effectiveLevel():
        discount = None
    subTotal = getTotal(orderItems, discount)
    alreadyPaid = staff.attendee.paidTotal()
    total = subTotal - alreadyPaid
    if total < 0: 
      return 0
    return total


def checkoutStaff(request):
    sessionItems = request.session.get('order_items', [])
    pdisc = request.session.get('discount', "")
    staffId = request.session['staff_id']
    orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
    postData = json.loads(request.body)
    event = Event.objects.first()
   
    #todo: event = Event.objects.get(id=int(postData["eventId"]))

    discount = Discount.objects.get(codeName="StaffDiscount")
    staff = Staff.objects.get(id=staffId)
    subtotal = getStaffTotal(orderItems, discount, staff)

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

    response = chargePayment(order.id, pbill, get_client_ip(request))

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
                    order.delete()
                    return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
        else:
            if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
            else:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.messages.message[0]['text'])})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': "Unknown Error"})

    request.session.flush()
    return JsonResponse({'success': True})



###################################
# Dealers

def dealers(request, guid):
    context = {'token': guid}
    return render(request, 'registration/dealer-locate.html', context)

def dealerAsst(request, guid):
    context = {'token': guid}
    return render(request, 'registration/dealerasst-locate.html', context)

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
    partnerCount = dealer.getPartnerCount()
    paidTotal = dealer.paidTotal()
    total = subTotal + 40*partnerCount + dealer.tableSize.basePrice - dealer.discount - paidTotal
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

def doneAsstDealer(request):
    context = {}
    return render(request, 'registration/dealerasst-done.html', context)

def findDealer(request):
  try:
    postData = json.loads(request.body)
    email = postData['email']
    token = postData['token']

    dealer = Dealer.objects.get(attendee__email__iexact=email, registrationToken=token)
    if not dealer:     
      return HttpResponseServerError("No Dealer Found")

    request.session['dealer_id'] = dealer.id
    return JsonResponse({'success': True, 'message':'DEALER'})
  except Exception as e:
    return HttpResponseServerError(str(e))

def findAsstDealer(request):
  try:
    postData = json.loads(request.body)
    email = postData['email']
    token = postData['token']

    dealer = Dealer.objects.get(attendee__email__iexact=email, registrationToken=token)
    if not dealer:     
      return HttpResponseServerError("No Dealer Found")

    request.session['dealer_id'] = dealer.id
    return JsonResponse({'success': True, 'message':'DEALER'})
  except Exception as e:
    return HttpResponseServerError(str(e))

def addAsstDealer(request):
    context = {'attendee': None, 'dealer': None}
    try:
      dealerId = request.session['dealer_id']
    except Exception as e:
      return render(request, 'registration/dealerasst-add.html', context)

    dealer = Dealer.objects.get(id=dealerId)
    if dealer.attendee:
      context = {'attendee': dealer.attendee, 'dealer': dealer}
    return render(request, 'registration/dealerasst-add.html', context)

def checkoutAsstDealer(request):
    postData = json.loads(request.body)
    pbill = postData["billingData"]
    assts = postData['assistants']
    dealerId = request.session['dealer_id']
    dealer = Dealer.objects.get(id=dealerId)

    priceLevel = dealer.attendee.effectiveLevel()
    if priceLevel is None:
        return JsonResponse({'success': False, 'message': "Dealer acount has not been paid. Please pay for your table before adding assistants."})

    originalPartnerCount = dealer.getPartnerCount()

    orderItem = OrderItem(attendee=dealer.attendee, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    dealer.partners = assts
    dealer.save()
    partnerCount = dealer.getPartnerCount()

    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    partners = partnerCount - originalPartnerCount

    order = Order(total=Decimal(40*partners), reference=reference, discount=None,
                  orgDonation=0, charityDonation=0, billingName=pbill['cc_firstname'] + " " + pbill['cc_lastname'],
                  billingAddress1=pbill['address1'], billingAddress2=pbill['address2'],
                  billingCity=pbill['city'], billingState=pbill['state'], billingCountry=pbill['country'],
                  billingPostal=pbill['postal'], billingEmail=pbill['email'])
    order.save()

    orderItem.order = order
    orderItem.save()
    
    response = chargePayment(order.id, pbill, get_client_ip(request))
    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages') == True:
                sendDealerAsstEmail(dealer.id)
                orderItem.order = order
                orderItem.save()
                request.session.flush()
                return JsonResponse({'success': True})
            else:
                if hasattr(response.transactionResponse, 'errors') == True:
                    order.delete()
                    return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
        else:
            if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
            else:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.messages.message[0]['text'])})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': "Unknown Error"})


    request.session.flush()
    return JsonResponse({'success': True})


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

    response = chargePayment(order.id, pbill, get_client_ip(request))

    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages') == True:
                orderItem.order = order
                orderItem.save()    
                sendDealerPaymentEmail(dealer, order)
                request.session.flush()
                return JsonResponse({'success': True})
            else:
                if hasattr(response.transactionResponse, 'errors') == True:
                    order.delete()
                    return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
        else:
            if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
            else:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.messages.message[0]['text'])})
    else:
        order.delete()
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
# Attendees - Onsite

def onsite(request):
    event = Event.objects.first()
    tz = timezone.get_current_timezone()
    today = tz.localize(datetime.now())
    context = {}
    if event.onlineRegStart <= today <= event.onlineRegEnd:
        return render(request, 'registration/onsite.html', context)
    return render(request, 'registration/closed.html', context)

def onsiteCart(request):
    sessionItems = request.session.get('order_items', [])
    if not sessionItems:
        context = {'orderItems': [], 'total': 0}
        request.session.flush()
    else:
        orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
        total = getTotal(orderItems)
        context = {'orderItems': orderItems, 'total': total}
    return render(request, 'registration/onsite-checkout.html', context)

def onsiteDone(request):
    context = {}
    request.session.flush()
    return render(request, 'registration/onsite-done.html', context)


###################################
# Attendees

def upgrade(request, guid):
    context = {'token': guid}
    return render(request, 'registration/attendee-locate.html', context)

def infoUpgrade(request):
  try:
    postData = json.loads(request.body)
    email = postData['email']
    token = postData['token']

    attendee = Attendee.objects.get(email__iexact=email, registrationToken=token)
    if not attendee:     
      return HttpResponseServerError("No Record Found")

    request.session['attendee_id'] = attendee.id
    return JsonResponse({'success': True, 'message':'ATTENDEE'})
  except Exception as e:
    return HttpResponseServerError(str(e))

def findUpgrade(request):
    context = {'attendee': None}
    try:
      attId = request.session['attendee_id']
    except Exception as e:
      return render(request, 'registration/attendee-upgrade.html', context)

    attendee = Attendee.objects.get(id=attId)
    if attendee:
        attendee_dict = model_to_dict(attendee)
        lvl_dict = model_to_dict(attendee.effectiveLevel())
        context = {'attendee': attendee,  
                   'jsonAttendee': json.dumps(attendee_dict, default=handler),
                   'jsonLevel': json.dumps(lvl_dict, default=handler)}
    return render(request, 'registration/attendee-upgrade.html', context)

def addUpgrade(request):
    postData = json.loads(request.body)
    pda = postData['attendee']
    pdp = postData['priceLevel']

    if 'attendee_id' not in request.session:
        return HttpResponseServerError("Session expired")

    ## Update Attendee info
    attendee = Attendee.objects.get(id=pda['id'])
    if not attendee:
        return HttpResponseServerError("Attendee id not found")

    priceLevel = PriceLevel.objects.get(id=int(pdp['id']))

    orderItem = OrderItem(attendee=attendee, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    for option in pdp['options']:
        plOption = PriceLevelOption.objects.get(id=int(option['id']))
        attendeeOption = AttendeeOptions(option=plOption, orderItem=orderItem, optionValue=option['value'])
        attendeeOption.save()

    orderItems = request.session.get('order_items', [])
    orderItems.append(orderItem.id)
    request.session['order_items'] = orderItems

    return JsonResponse({'success': True})

def invoiceUpgrade(request):
    sessionItems = request.session.get('order_items', [])
    if not sessionItems:
        context = {'orderItems': [], 'total': 0, 'discount': {}}
        request.session.flush()
    else:
        attendeeId = request.session.get('attendee_id', -1)
        if attendeeId == -1: 
            context = {'orderItems': [], 'total': 0, 'discount': {}}
            request.session.flush()
        else:
            attendee = Attendee.objects.get(id=attendeeId)
            orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
            total = getTotal(orderItems)
            context = {'orderItems': orderItems, 'total': total, 'attendee': attendee}
    return render(request, 'registration/upgrade-checkout.html', context)

def doneUpgrade(request):
    context = {}
    return render(request, 'registration/upgrade-done.html', context)

def checkoutUpgrade(request):
  try:
    sessionItems = request.session.get('order_items', [])
    orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
    orderItem = orderItems[0]
    if 'attendee_id' not in request.session:
        return HttpResponseServerError("Session expired")

    attendee = Attendee.objects.get(id=request.session.get('attendee_id'))
    postData = json.loads(request.body)
    event = Event.objects.first()

    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    subtotal = getTotal(orderItems)

    if subtotal == 0:
        att = attendee
        order = Order(total=0, reference=reference, discount=None,
                  orgDonation=0, charityDonation=0,
                  billingName=att.firstName + " " + att.lastName,
                  billingAddress1=att.address1, billingAddress2=att.address2,
                  billingCity=att.city, billingState=att.state, billingCountry=att.country,
                  billingPostal=att.postalCode, status="Complete")
        order.save()

        orderItem.order = order
        orderItem.save()
        sendUpgradePaymentEmail(attendee, order)
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
    order = Order(total=Decimal(total), reference=reference, discount=None,
                  orgDonation=porg, charityDonation=pcharity,
                  billingName=pbill['cc_firstname'] + " " + pbill['cc_lastname'],
                  billingAddress1=pbill['address1'], billingAddress2=pbill['address2'],
                  billingCity=pbill['city'], billingState=pbill['state'], billingCountry=pbill['country'],
                  billingPostal=pbill['postal'])
    order.save()

    response = chargePayment(order.id, pbill, get_client_ip(request))

    if response is not None:
        if response.messages.resultCode == "Ok":
            if hasattr(response.transactionResponse, 'messages') == True:
                orderItem.order = order
                orderItem.save()    
                sendUpgradePaymentEmail(attendee, order)
                request.session.flush()
                return JsonResponse({'success': True})
            else:
                if hasattr(response.transactionResponse, 'errors') == True:
                    order.delete()
                    return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
        else:
            if hasattr(response, 'transactionResponse') == True and hasattr(response.transactionResponse, 'errors') == True:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.transactionResponse.errors.error[0].errorText)})
            else:
                order.delete()
                return JsonResponse({'success': False, 'message': str(response.messages.message[0]['text'])})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': "Unknown Error"})
        
  except Exception as e:
    return HttpResponseServerError(str(e))



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
    evt = postData['event']

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda['birthdate'], '%m/%d/%Y' ))

    event = Event.objects.get(name=evt)

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
        request.session.flush()
        sendRegistrationEmail(order.id, att.email)
        return JsonResponse({'success': True})

    porg = Decimal(postData["orgDonation"].strip() or 0.00)
    pcharity = Decimal(postData["charityDonation"].strip() or 0.00)
    pbill = postData["billingData"]

    if porg < 0: 
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity

    onsite = postData["onsite"]
    if onsite:
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
        request.session.flush()
        return JsonResponse({'success': True})
    


    order = Order(total=Decimal(total), reference=reference, discount=discount,
                  orgDonation=porg, charityDonation=pcharity, billingName=pbill['cc_firstname'] + " " + pbill['cc_lastname'],
                  billingAddress1=pbill['address1'], billingAddress2=pbill['address2'],
                  billingCity=pbill['city'], billingState=pbill['state'], billingCountry=pbill['country'],
                  billingPostal=pbill['postal'], billingEmail=pbill['email'])
    order.save()

    response = chargePayment(order.id, pbill, get_client_ip(request))

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
# Printing

def printNametag(request):
    context = { 'file' : request.GET.get('file', None) }
    return render(request, 'registration/printing.html', context)

def servePDF(request):
    filename = request.GET.get('file', None)
    if filename is None:
        return JsonResponse({'success': False})
    filename = filename.replace('..', '/')
    try:
        fsock = open('/tmp/%s' % filename)
    except IOError as e:
        return JsonResponse({'success': False}) 
    response = HttpResponse(fsock, content_type='application/pdf')
    #response['Content-Disposition'] = 'attachment; filename=download.pdf'
    fsock.close()
    os.unlink('/tmp/%s' % filename)
    return response


###################################
# Utilities

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def getOptionsDict(orderItems):
    orderDict = {}
    for oi in orderItems:
        aos = oi.getOptions()
        for ao in aos: 
            if ao.optionValue == 0 or ao.optionValue == None or ao.optionValue == "": pass
            if ao.option.optionName in orderDict: 
              orderDict[ao.option.optionName.replace(" ", "").replace("-", "") + '2'] = ao.optionValue
            else:
              orderDict[ao.option.optionName.replace(" ", "").replace("-", "")] = ao.optionValue

    return orderDict

def badgeList(request):
    attendees = Attendee.objects.all()
    staff = Staff.objects.all()

    data = [{'firstName': att.firstName.lower(), 'lastName': att.lastName.lower(), 'badgeName': att.badgeName, 
             'badgeNumber': att.badgeNumber, 'level': att.effectiveLevel().name, 'printed': att.printed,
             'assoc': att.abandoned(), 'orderItems':getOptionsDict(att.orderitem_set.all()), 
             'discount': att.getDiscount()} for att in attendees if att.effectiveLevel() != None]
    staffdata = [{'firstName': s.attendee.firstName.lower(), 'lastName':s.attendee.lastName.lower(),
                  'badgeName': s.attendee.badgeName, 'badgeNumber': s.attendee.badgeNumber, 
                  'level': s.attendee.effectiveLevel().name, 'assoc': s.attendee.abandoned(), 
                  'orderItems':getOptionsDict(s.attendee.orderitem_set.all()), 
                  'discount': s.attendee.getDiscount(), 
                  'title': s.title} for s in staff if s.attendee.effectiveLevel() != None]

    sdata = sorted(data, key=lambda x:(x['level'],x['lastName']))
    ssdata = sorted(staffdata, key=lambda x:x['lastName'])

    dealers = [att for att in sdata if att['assoc'] == 'Dealer']
    staff = [att for att in ssdata]
    attendees = [att for att in sdata if att['assoc'] != 'Staff' ]
    return render(request, 'registration/utility/badgelist.html', {'attendees': attendees, 'dealers': dealers, 'staff': staff})    


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

def getMinorPriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=False, startDate__lte=now, endDate__gte=now, name__icontains='minor').order_by('basePrice')
    data = [{'name': level.name, 'id':level.id,  'base_price': level.basePrice.__str__(), 'description': level.description,'options': [{'name': option.optionName, 'value': option.optionPrice, 'id': option.id, 'required': option.required, 'active': option.active, 'type': option.optionExtraType, "list": option.getList() } for option in level.priceleveloption_set.order_by('optionPrice').all() ]} for level in levels]
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def getAccompaniedPriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=False, startDate__lte=now, endDate__gte=now, name__icontains='accompanied').order_by('basePrice')
    data = [{'name': level.name, 'id':level.id,  'base_price': level.basePrice.__str__(), 'description': level.description,'options': [{'name': option.optionName, 'value': option.optionPrice, 'id': option.id, 'required': option.required, 'active': option.active, 'type': option.optionExtraType, "list": option.getList() } for option in level.priceleveloption_set.order_by('optionPrice').all() ]} for level in levels]
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def getFreePriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=False, startDate__lte=now, endDate__gte=now, name__icontains='free')
    data = [{'name': level.name, 'id':level.id,  'base_price': level.basePrice.__str__(), 'description': level.description,'options': [{'name': option.optionName, 'value': option.optionPrice, 'id': option.id, 'required': option.required, 'active': option.active, 'type': option.optionExtraType, "list": option.getList() } for option in level.priceleveloption_set.order_by('optionPrice').all() ]} for level in levels]
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')


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
    data = [{'name': level.name, 'id':level.id,  'base_price': level.basePrice.__str__(), 'description': level.description,'options': [{'name': option.optionName, 'value': option.optionPrice, 'id': option.id, 'required': option.required, 'active': option.active, 'type': option.optionExtraType, "list": option.getList() } for option in level.priceleveloption_set.order_by('optionPrice').all() ]} for level in levels]
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
                if option.optionValue:
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

