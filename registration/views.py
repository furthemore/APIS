from django.contrib.admin.views.decorators import staff_member_required
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseServerError, JsonResponse
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

import time
from datetime import datetime, date
from decimal import *
from operator import itemgetter
import itertools
import os
import json
import random
import string
import logging

from .emails import *
from .models import *
from .payments import chargePayment
from .pushy import PushyAPI
import printing

# Create your views here.
logger = logging.getLogger("django.request")

def index(request):
    event = Event.objects.get(default=True)
    tz = timezone.get_current_timezone()
    today = tz.localize(datetime.now())
    context = {'event':event}
    if event.attendeeRegStart <= today <= event.attendeeRegEnd:
        return render(request, 'registration/registration-form.html', context)
    return render(request, 'registration/closed.html', context)

def flush(request):
    request.session.flush()
    return JsonResponse({'success': True})


###################################
# Payments

def doCheckout(billingData, total, discount, orderItems, donationOrg, donationCharity, ip):
    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    order = Order(total=Decimal(total), reference=reference, discount=discount,
                  orgDonation=donationOrg, charityDonation=donationCharity,
                  billingName=billingData['cc_firstname'] + " " + billingData['cc_lastname'],
                  billingAddress1=billingData['address1'], billingAddress2=billingData['address2'],
                  billingCity=billingData['city'], billingState=billingData['state'], billingCountry=billingData['country'],
                  billingPostal=billingData['postal'], billingEmail=billingData['email'])
    order.save()

    status, response = chargePayment(order.id, billingData, ip)

    if status:
        for oitem in orderItems:
            oitem.order = order
            oitem.save()
        order.status = 'Paid'
        order.save()
        if discount:
            discount.used = discount.used + 1
            discount.save()
        return True, "", order

    return False, response, order


def doZeroCheckout(attendee, discount, orderItems):
    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    order = Order(total=0, reference=reference, discount=discount,
                  orgDonation=0, charityDonation=0, billingName=attendee.firstName + " " + attendee.lastName,
                  billingAddress1=attendee.address1, billingAddress2=attendee.address2,
                  billingCity=attendee.city, billingState=attendee.state, billingCountry=attendee.country,
                  billingPostal=attendee.postalCode, billingEmail=attendee.email, status="Complete")
    order.save()
    email = attendee.email

    for oitem in orderItems:
        oitem.order = order
        oitem.save()

    if discount:
        discount.used = discount.used + 1
        discount.save()
    return True, "", order


def getTotal(orderItems, disc = ""):
    total = 0
    if not orderItems: return total
    for item in orderItems:
        itemSubTotal = item.priceLevel.basePrice
        effLevel = item.badge.effectiveLevel()
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

def getDealerTotal(orderItems, dealer):
    itemSubTotal = 0
    for item in orderItems:
        itemSubTotal = item.priceLevel.basePrice
        for option in item.attendeeoptions_set.all():
            if option.option.optionExtraType == 'int':
                if option.optionValue:
                    itemSubTotal += (option.option.optionPrice*Decimal(option.optionValue))
            else:
                itemSubTotal += option.option.optionPrice

    partnerCount = dealer.getPartnerCount()
    partnerBreakfast = 0
    if partnerCount > 0 and dealer.asstBreakfast:
      partnerBreakfast = 60*partnerCount
    wifi = 0
    if dealer.needWifi:
        wifi = 50
    total = itemSubTotal + 45*partnerCount + partnerBreakfast + dealer.tableSize.basePrice + wifi - dealer.discount
    if total < 0:
      return 0
    return total

def applyDiscount(request):
    dis = request.session.get('discount', "")
    if dis:
        return JsonResponse({'success': False, 'message': 'Only one discount is allowed per order.'})

    postData = json.loads(request.body)
    dis = postData['discount']

    discount = Discount.objects.filter(codeName=dis)
    if discount.count() == 0:
        return JsonResponse({'success': False, 'message': 'That discount is not valid.'})
    discount = discount.first()
    if not discount.isValid():
        return JsonResponse({'success': False, 'message': 'That discount is not valid.'})

    request.session["discount"] = discount.codeName
    return JsonResponse({'success': True})


###################################
# New Staff

def newStaff(request, guid):
    event = Event.objects.get(default=True)
    context = {'token': guid, 'event': event}
    return render(request, 'registration/staff/staff-new.html', context)

def findNewStaff(request):
  try:
    postData = json.loads(request.body)
    email = postData['email']
    token = postData['token']

    token = TempToken.objects.get(email=__iexactemail, token=token)
    if not token:
        return HttpResponseServerError("No Staff Found")

    if token.validUntil < timezone.now():
        return HttpResponseServerError("Invalid Token")
    if token.used:
        return HttpResponseServerError("Token Used")

    request.session["newStaff"] = token.token

    return JsonResponse({'success': True, 'message':'STAFF'})
  except Exception as e:
    logger.exception("Unable to find staff." + request.body)
    return HttpResponseServerError(str(e))

def infoNewStaff(request):
    event = Event.objects.get(default=True)
    try:
      tokenValue = request.session["newStaff"]
      token = TempToken.objects.get(token=tokenValue)
    except Exception as e:
      token = None
    context = {'staff': None, 'event': event, 'token': token}
    return render(request, 'registration/staff/staff-new-payment.html', context)

def addNewStaff(request):
    postData = json.loads(request.body)
    #create attendee from request post
    pda = postData['attendee']
    pds = postData['staff']
    pdp = postData['priceLevel']
    evt = postData['event']

    if evt:
      event = Event.objects.get(name=evt)
    else:
      event = Event.objects.get(default=True)

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda['birthdate'], '%Y-%m-%d' ))

    attendee = Attendee(firstName=pda['firstName'], lastName=pda['lastName'], address1=pda['address1'], address2=pda['address2'],
                        city=pda['city'], state=pda['state'], country=pda['country'], postalCode=pda['postal'],
                        phone=pda['phone'], email=pda['email'], birthdate=birthdate,
                        emailsOk=True, surveyOk=False)
    attendee.save()

    badge = Badge(attendee=attendee, event=event, badgeName=pda['badgeName'])
    badge.save()

    shirt = ShirtSizes.objects.get(id=pds['shirtsize'])

    staff = Staff(attendee=attendee, event=event)
    staff.twitter = pds['twitter']
    staff.telegram = pds['telegram']
    staff.shirtsize = shirt
    staff.specialSkills = pds['specialSkills']
    staff.specialFood = pds['specialFood']
    staff.specialMedical = pds['specialMedical']
    staff.contactName = pds['contactName']
    staff.contactPhone = pds['contactPhone']
    staff.contactRelation = pds['contactRelation']
    staff.save()

    priceLevel = PriceLevel.objects.get(id=int(pdp['id']))

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    for option in pdp['options']:
        plOption = PriceLevelOption.objects.get(id=int(option['id']))
        attendeeOption = AttendeeOptions(option=plOption, orderItem=orderItem, optionValue=option['value'])
        attendeeOption.save()

    orderItems = request.session.get('order_items', [])
    orderItems.append(orderItem.id)
    request.session['order_items'] = orderItems

    discount = event.newStaffDiscount
    if discount:
        request.session["discount"] = discount.codeName

    tokens = TempToken.objects.filter(email=attendee.email)
    for token in tokens:
        token.used = True
        token.save()

    return JsonResponse({'success': True})



###################################
# Staff

def staff(request, guid):
    event = Event.objects.get(default=True)
    context = {'token': guid, 'event': event}
    return render(request, 'registration/staff/staff-locate.html', context)


def staffDone(request):
    event = Event.objects.get(default=True)
    context = {'event': event}
    return render(request, 'registration/staff/staff-done.html', context)


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
    logger.exception("Unable to find staff." + request.body)
    return HttpResponseServerError(str(e))


def infoStaff(request):
    event = Event.objects.get(default=True)
    context = {'staff': None, 'event': event}
    try:
      staffId = request.session['staff_id']
    except Exception as e:
      return render(request, 'registration/staff-payment.html', context)

    staff = Staff.objects.get(id=staffId)
    if staff:
        staff_dict = model_to_dict(staff)
        attendee_dict = model_to_dict(staff.attendee)
        badges = Badge.objects.filter(attendee=staff.attendee,event=staff.event)

        badge = {}
        if badges.count() > 0:
            badge = badges[0]

        context = {'staff': staff, 'jsonStaff': json.dumps(staff_dict, default=handler),
                   'jsonAttendee': json.dumps(attendee_dict, default=handler),
                   'badge': badge, 'event': event}
    return render(request, 'registration/staff/staff-payment.html', context)


def addStaff(request):
    postData = json.loads(request.body)
    #create attendee from request post
    pda = postData['attendee']
    pds = postData['staff']
    pdp = postData['priceLevel']
    evt = postData['event']

    if evt:
      event = Event.objects.get(name=evt)
    else:
      event = Event.objects.get(default=True)

    attendee = Attendee.objects.get(id=pda['id'])
    if not attendee:
        return JsonResponse({'success': False, 'message': 'Attendee not found'})

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda['birthdate'], '%Y-%m-%d' ))

    attendee.firstName=pda['firstName']
    attendee.lastName=pda['lastName']
    attendee.address1=pda['address1']
    attendee.address2=pda['address2']
    attendee.city=pda['city']
    attendee.state=pda['state']
    attendee.country=pda['country']
    attendee.postalCode=pda['postal']
    attendee.birthdate=birthdate
    attendee.phone=pda['phone']
    attendee.emailsOk=True
    attendee.surveyOk=False  #staff get their own survey

    try:
        attendee.save()
    except Exception as e:
        logger.exception("Error saving staff attendee record.")
        return JsonResponse({'success': False, 'message': 'Attendee not saved: ' + e})

    staff = Staff.objects.get(id=pds['id'])
    if 'staff_id' not in request.session:
        return JsonResponse({'success': False, 'message': 'Staff record not found'})

    ## Update Staff info
    if not staff:
        return JsonResponse({'success': False, 'message': 'Staff record not found'})

    shirt = ShirtSizes.objects.get(id=pds['shirtsize'])
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
        logger.exception("Error saving staff record.")
        return JsonResponse({'success': False, 'message': 'Staff not saved: ' + str(e)})

    badges = Badge.objects.filter(attendee=attendee,event=event)
    if badges.count() == 0:
        badge = Badge(attendee=attendee,event=event,badgeName=pda['badgeName'])
    else:
        badge = badges[0]
        badge.badgeName = pda['badgeName']

    try:
        badge.save()
    except Exception as e:
        logger.exception("Error saving staff badge record.")
        return JsonResponse({'success': False, 'message': 'Badge not saved: ' + str(e)})

    priceLevel = PriceLevel.objects.get(id=int(pdp['id']))

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    for option in pdp['options']:
        plOption = PriceLevelOption.objects.get(id=int(option['id']))
        attendeeOption = AttendeeOptions(option=plOption, orderItem=orderItem, optionValue=option['value'])
        attendeeOption.save()

    orderItems = request.session.get('order_items', [])
    orderItems.append(orderItem.id)
    request.session['order_items'] = orderItems

    discount = event.staffDiscount
    if discount:
        request.session["discount"] = discount.codeName

    staff.resetToken()

    return JsonResponse({'success': True})


###################################
# Dealers

def dealers(request, guid):
    event = Event.objects.get(default=True)
    context = {'token': guid, 'event': event}
    return render(request, 'registration/dealer/dealer-locate.html', context)

def thanksDealer(request):
    event = Event.objects.get(default=True)
    context = {'event': event}
    return render(request, 'registration/dealer/dealer-thanks.html', context)

def updateDealer(request):
    context = {}
    return render(request, 'registration/dealer/dealer-update.html', context)

def doneDealer(request):
    event = Event.objects.get(default=True)
    context = {'event': event}
    return render(request, 'registration/dealer/dealer-done.html', context)

def dealerAsst(request, guid):
    context = {'token': guid}
    return render(request, 'registration/dealer/dealerasst-locate.html', context)

def doneAsstDealer(request):
    context = {}
    return render(request, 'registration/dealer/dealerasst-done.html', context)

def newDealer(request):
    event = Event.objects.get(default=True)
    tz = timezone.get_current_timezone()
    today = tz.localize(datetime.now())
    context = {'event': event}
    if event.dealerRegStart <= today <= event.dealerRegEnd:
        return render(request, 'registration/dealer/dealer-form.html', context)
    return render(request, 'registration/dealer/dealer-closed.html', context)

def infoDealer(request):
    event = Event.objects.get(default=True)
    context = {'dealer': None, 'event':event}
    try:
      dealerId = request.session['dealer_id']
    except Exception as e:
      return render(request, 'registration/dealer/dealer-payment.html', context)

    dealer = Dealer.objects.get(id=dealerId)
    if dealer:
        badge = Badge.objects.filter(attendee=dealer.attendee, event=dealer.event).last()
        dealer_dict = model_to_dict(dealer)
        attendee_dict = model_to_dict(dealer.attendee)
        badge_dict = model_to_dict(badge)
        table_dict = model_to_dict(dealer.tableSize)

        context = {'dealer': dealer, 'badge': badge, 'event': dealer.event,
                   'jsonDealer': json.dumps(dealer_dict, default=handler),
                   'jsonTable': json.dumps(table_dict, default=handler),
                   'jsonAttendee': json.dumps(attendee_dict, default=handler),
                   'jsonBadge': json.dumps(badge_dict, default=handler)}
    return render(request, 'registration/dealer/dealer-payment.html', context)

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
    logger.exception("Error finding dealer.")
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
    logger.exception("Error finding assistant dealer.")
    return HttpResponseServerError(str(e))


def addAsstDealer(request):
    context = {'attendee': None, 'dealer': None}
    try:
      dealerId = request.session['dealer_id']
    except Exception as e:
      return render(request, 'registration/dealer/dealerasst-add.html', context)

    dealer = Dealer.objects.get(id=dealerId)
    if dealer.attendee:
      context = {'attendee': dealer.attendee, 'dealer': dealer}
    return render(request, 'registration/dealer/dealerasst-add.html', context)

def checkoutAsstDealer(request):
    postData = json.loads(request.body)
    pbill = postData["billingData"]
    assts = postData['assistants']
    dealerId = request.session['dealer_id']
    dealer = Dealer.objects.get(id=dealerId)

    badge = Badge.objects.filter(attendee=dealer.attendee, event=dealer.event).last()

    priceLevel = badge.effectiveLevel()
    if priceLevel is None:
        return JsonResponse({'success': False, 'message': "Dealer acocunt has not been paid. Please pay for your table before adding assistants."})

    originalPartnerCount = dealer.getPartnerCount()

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    dealer.partners = assts
    dealer.save()
    partnerCount = dealer.getPartnerCount()

    partners = partnerCount - originalPartnerCount
    total = Decimal(45*partners)
    if pbill['breakfast']:
        total = total + Decimal(60*partners)
    ip = get_client_ip(request)

    status, message, order = doCheckout(pbill, total, None, [orderItem], 0, 0, ip)

    if status:
        request.session.flush()
        try:
            sendDealerAsstEmail(dealer.id)
        except Exception as e:
            logger.exception("Error emailing DealerAsstEmail.")
            return JsonResponse({'success': False, 'message': "Your payment succeeded but we may have been unable to send you a confirmation email. If you do not receive one within the next hour, please contact marketplace@furthemore.org to get your confirmation number."})
        return JsonResponse({'success': True})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': message})


def addDealer(request):
    postData = json.loads(request.body)
    pda = postData['attendee']
    pdd = postData['dealer']
    evt = postData['event']
    pdp = postData['priceLevel']
    event = Event.objects.get(name=evt)

    if 'dealer_id' not in request.session:
        return HttpResponseServerError("Session expired")

    dealer = Dealer.objects.get(id=pdd['id'])

    ## Update Dealer info
    if not dealer:
        return HttpResponseServerError("Dealer id not found")

    dealer.businessName=pdd['businessName']
    dealer.website=pdd['website']
    dealer.logo=pdd['logo']
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
    dealer.asstBreakfast=pdd['asstbreakfast']
    dealer.event = event

    try:
        dealer.save()
    except Exception as e:
        logger.exception("Error saving dealer record.")
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

    try:
        attendee.save()
    except Exception as e:
        logger.exception("Error saving dealer attendee record.")
        return HttpResponseServerError(str(e))


    badge = Badge.objects.get(attendee=attendee,event=event)
    badge.badgeName=pda['badgeName']

    try:
        badge.save()
    except Exception as e:
        logger.exception("Error saving dealer badge record.")
        return HttpResponseServerError(str(e))


    priceLevel = PriceLevel.objects.get(id=int(pdp['id']))

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    for option in pdp['options']:
        plOption = PriceLevelOption.objects.get(id=int(option['id']))
        attendeeOption = AttendeeOptions(option=plOption, orderItem=orderItem, optionValue=option['value'])
        attendeeOption.save()

    orderItems = request.session.get('order_items', [])
    orderItems.append(orderItem.id)
    request.session['order_items'] = orderItems

    return JsonResponse({'success': True})

def invoiceDealer(request):
    sessionItems = request.session.get('order_items', [])
    if not sessionItems:
        context = {'orderItems': [], 'total': 0}
        request.session.flush()
    else:
        dealerId = request.session.get('dealer_id', -1)
        if dealerId == -1:
            context = {'orderItems': [], 'total': 0}
            request.session.flush()
        else:
            dealer = Dealer.objects.get(id=dealerId)
            orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
            total = getDealerTotal(orderItems, dealer)
            context = {'orderItems': orderItems, 'total': total, 'dealer': dealer}
    return render(request, 'registration/dealer/dealer-checkout.html', context)

def checkoutDealer(request):
  try:
    sessionItems = request.session.get('order_items', [])
    orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
    orderItem = orderItems[0]
    if 'dealer_id' not in request.session:
        return HttpResponseServerError("Session expired")

    dealer = Dealer.objects.get(id=request.session.get('dealer_id'))
    postData = json.loads(request.body)

    subtotal = getDealerTotal(orderItems, dealer)

    if subtotal == 0:

      status, message, order = doZeroCheckout(dealer.attendee, None, orderItems)
      if not status:
          return JsonResponse({'success': False, 'message': message})

      request.session.flush()

      try:
          dealer.resetToken()
          sendDealerPaymentEmail(dealer, order)
      except Exception as e:
          logger.exception("Error sending DealerPaymentEmail - zero sum.")
          return JsonResponse({'success': False, 'message': "Your registration succeeded but we may have been unable to send you a confirmation email. If you have any questions, please contact marketplace@furthemore.org."})
      return JsonResponse({'success': True})

    porg = Decimal(postData["orgDonation"].strip() or 0.00)
    pcharity = Decimal(postData["charityDonation"].strip() or 0.00)
    if porg < 0:
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity

    pbill = postData['billingData']
    ip = get_client_ip(request)
    status, message, order = doCheckout(pbill, total, None, orderItems, porg, pcharity, ip)

    if status:
        request.session.flush()
        try:
            dealer.resetToken()
            sendDealerPaymentEmail(dealer, order)
        except Exception as e:
            logger.exception("Error sending DealerPaymentEmail." + request.body)
            return JsonResponse({'success': False, 'message': "Your registration succeeded but we may have been unable to send you a confirmation email. If you have any questions, please contact marketplace@furthemore.org."})
        return JsonResponse({'success': True})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': message})
  except Exception as e:
    logger.exception("Error in dealer checkout." + request.body)
    return HttpResponseServerError(str(e))


def addNewDealer(request):
  try:
    postData = json.loads(request.body)
    #create attendee from request post
    pda = postData['attendee']
    pdd = postData['dealer']
    evt = postData['event']

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda['birthdate'], '%Y-%m-%d' ))
    event = Event.objects.get(name=evt)

    attendee = Attendee(firstName=pda['firstName'], lastName=pda['lastName'], address1=pda['address1'], address2=pda['address2'],
                        city=pda['city'], state=pda['state'], country=pda['country'], postalCode=pda['postal'],
                        phone=pda['phone'], email=pda['email'], birthdate=birthdate,
                        emailsOk=bool(pda['emailsOk']), surveyOk=bool(pda['surveyOk'])
                        )
    attendee.save()

    badge = Badge(attendee=attendee, event=event, badgeName=pda['badgeName'])
    badge.save()

    tablesize = TableSize.objects.get(id=pdd['tableSize'])
    dealer = Dealer(attendee=attendee, event=event, businessName=pdd['businessName'], logo=pdd['logo'],
                    website=pdd['website'], description=pdd['description'], license=pdd['license'], needPower=pdd['power'],
                    needWifi=pdd['wifi'], wallSpace=pdd['wall'], nearTo=pdd['near'], farFrom=pdd['far'], tableSize=tablesize,
                    chairs=pdd['chairs'], reception=pdd['reception'], artShow=pdd['artShow'], charityRaffle=pdd['charityRaffle'],
                    breakfast=pdd['breakfast'], willSwitch=pdd['switch'], tables=pdd['tables'],
                    agreeToRules=pdd['agreeToRules'], buttonOffer=pdd['buttonOffer'], asstBreakfast=pdd['asstbreakfast']
                    )
    dealer.save()

    partners = pdd['partners']
    for partner in partners:
        dealerPartner = DealerAsst(dealer=dealer, event=event, name=partner['name'],
                                   email=partner['email'], license=partner['license'])
        dealerPartner.save()


    try:
        sendDealerApplicationEmail(dealer.id)
    except Exception as e:
        logger.exception("Error sending DealerApplicationEmail." + request.body)
        return JsonResponse({'success': False, 'message': "Your registration succeeded but we may have been unable to send you a confirmation email. If you have any questions, please contact marketplace@furthemore.org."})
    return JsonResponse({'success': True})

  except Exception as e:
    logger.exception("Error in dealer addition." + request.body)
    return HttpResponseServerError(str(e))


###################################
# Attendees - Onsite

def onsite(request):
    event = Event.objects.get(default=True)
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

@staff_member_required
def onsiteAdmin(request):
    # Modify a dummy session variable to keep it alive
    request.session['heartbeat'] = time.time()

    terminals = list(Firebase.objects.all())
    term = request.session.get('terminal', None)
    query = request.GET.get('search', None)

    errors = []
    results = None

    # Set default payment terminal to use:
    if term is None and len(terminals) > 0:
        request.session['terminal'] = terminals[0].id

    # No terminal selection saved in session - see if one's
    # on the URL (that way it'll survive session timeouts)
    url_terminal = request.GET.get('terminal', None)
    logger.info("Terminal from GET parameter: {0}".format(url_terminal))
    if url_terminal is not None:
        try:
            terminal_obj = Firebase.objects.get(id=int(url_terminal))
            request.session['terminal'] = terminal_obj.id
        except Firebase.DoesNotExist:
            errors.append({'type' : 'warning', 'text' : 'The payment terminal specified has not registered with the server'})
        except ValueError:
            # weren't passed an integer
            errors.append({'type' : 'danger', 'text' : 'Invalid terminal specified'})


    logger.info("Terminal from session: {0}".format(request.session['terminal']))


    if query is not None:
        results = Badge.objects.filter(
            Q(attendee__lastName__icontains=query) | Q(attendee__firstName__icontains=query),
            Q(event__name__icontains='2018')
        )
        if len(results) == 0:
            errors.append({'type' : 'warning', 'text' : 'No results for query "{0}"'.format(query)})

    context = {
        'terminals' : terminals,
        'errors' : errors,
        'results' : results
    }

    return render(request, 'registration/onsite-admin.html', context)

@staff_member_required
def onsiteAdminSearch(request):
    terminals = list(Firebase.objects.all())
    query = request.POST.get('search', None)
    if query is None:
        return redirect('onsiteAdmin')

    errors = []
    results = Badge.objects.filter(
        Q(attendee__lastName__icontains=query) | Q(attendee__firstName__icontains=query),
        Q(event__name__icontains='2018')
    )
    if len(results) == 0:
        errors = [{'type' : 'warning', 'text' : 'No results for query "{0}"'.format(query)}]

    context = {
        'terminals' : terminals,
        'errors' : errors,
        'results' : results
    }
    return render(request, 'registration/onsite-admin.html', context)

def get_age(obj):
    born = obj.attendee.birthdate
    today = date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age

@staff_member_required
def onsiteAdminCart(request):
    # Returns dataset to render onsite cart preview
    request.session['heartbeat'] = time.time()  # Keep session alive
    cart = request.session.get('cart', None)
    if cart is None:
        return JsonResponse({'success' : False, 'reason' : 'Cart not initialized'})

    badges = []
    for id in cart:
        try:
            badge = Badge.objects.get(id=id)
            badges.append(badge)
        except Badge.DoesNotExist:
            cart.remove(id)
            logger.error("ID {0} was in cart but doesn't exist in the database".format(id))

    order = None
    subtotal = 0
    result = []
    for badge in badges:
        oi = badge.getOrderItems()
        level = None
        for item in oi:
            level = item.priceLevel
            if item.order is not None:
                order = item.order
        if level is None:
            effectiveLevel = None
        else:
            effectiveLevel = {
                'name' : level.name,
                'price' : level.basePrice
            }
            subtotal += level.basePrice

        item = {
            'id' : badge.id,
            'firstName' : badge.attendee.firstName,
            'lastName' : badge.attendee.lastName,
            'badgeName' : badge.badgeName,
            'abandoned' : badge.abandoned,
            'effectiveLevel' : effectiveLevel,
            'discount' : badge.getDiscount(),
            'age' : get_age(badge)
        }
        result.append(item)

    total = subtotal
    charityDonation = '?'
    orgDonation = '?'
    if order is not None:
        total += order.orgDonation + order.charityDonation
        charityDonation = order.charityDonation
        orgDonation = order.orgDonation

    data = {
        'success' : True,
        'result' : result,
        'total' : total,
        'charityDonation' : charityDonation,
        'orgDonation' : orgDonation,
    }

    if order is not None:
        data['order_id'] = order.id
        data['reference'] = order.reference
    else:
        data['order_id'] = None
        data['reference'] = None

    notifyTerminal(request, data)

    return JsonResponse(data)

@staff_member_required
def onsiteAddToCart(request):
    id = request.GET.get('id', None)
    if id is None or id == '':
        return JsonResponse({'success' : False, 'reason' : 'Need ID parameter'}, status=400)

    cart = request.session.get('cart', None)
    if cart is None:
        request.session['cart'] = [id,]
        return JsonResponse({'success' : True, 'cart' : [id]})

    if id in cart:
        return JsonResponse({'success' : True, 'cart' : cart})

    cart.append(id)
    request.session['cart'] = cart

    return JsonResponse({'success' : True, 'cart' : cart})

@staff_member_required
def onsiteRemoveFromCart(request):
    id = request.GET.get('id', None)
    if id is None or id == '':
        return JsonResponse({'success' : False, 'reason' : 'Need ID parameter'}, status=400)

    cart = request.session.get('cart', None)
    if cart is None:
        return JsonResponse({'success' : False, 'reason' : 'Cart is empty'})

    try:
        cart.remove(id)
        request.session['cart'] = cart
    except ValueError:
        return JsonResponse({'success' : False, 'cart' : cart, 'reason' : 'Not in cart'})

    return JsonResponse({'success' : True, 'cart' : cart})

@staff_member_required
def onsiteAdminClearCart(request):
    request.session["cart"] = [];
    sendMessageToTerminal(request, {"command" : "clear"})
    return onsiteAdmin(request)

@staff_member_required
def closeTerminal(request):
    data = { "command" : "close" }
    return sendMessageToTerminal(request, data)

@staff_member_required
def openTerminal(request):
    data = { "command" : "open" }
    return sendMessageToTerminal(request, data)

def sendMessageToTerminal(request, data):
    request.session['heartbeat'] = time.time()  # Keep session alive
    url_terminal = request.GET.get('terminal', None)
    logger.info("Terminal from GET parameter: {0}".format(url_terminal))
    session_terminal = request.session.get('terminal', None)

    if url_terminal is not None:
        try:
            active = Firebase.objects.get(id=int(url_terminal))
            request.session['terminal'] = active.id
        except Firebase.DoesNotExist:
            return JsonResponse({'success' : False, 'message' : 'The payment terminal specified has not registered with the server'}, status=500)
        except ValueError:
            # weren't passed an integer
            return JsonResponse({'success' : False, 'message' : 'Invalid terminal specified'}, status=400)

    try:
        active = Firebase.objects.get(id=session_terminal)
    except Firebase.DoesNotExist:
        return JsonResponse({'success' : False, 'message' : 'No terminal specified and none in session'}, status=400)

    logger.info("Terminal from session: {0}".format(request.session['terminal']))

    to = [active.token,]

    PushyAPI.sendPushNotification(data, to, None)
    return JsonResponse({'success' : True})

@staff_member_required
def enablePayment(request):
    data = { "command" : "enable_payment" }
    return sendMessageToTerminal(request, data)


def notifyTerminal(request, data):
    # Generates preview layout based on cart items and sends the result
    # to the apropriate payment terminal for display to the customer
    term = request.session.get('terminal', None)
    if term is None:
        return
    try:
        active = Firebase.objects.get(id=term)
    except Firebase.DoesNotExist:
        return

    html = render_to_string('registration/customer-display.html', data)
    note = render_to_string('registration/customer-note.txt', data)

    logger.info(note)

    if len(data['result']) == 0:
        display = { "command" : "clear" }
    else:
        display = {
            "command" : "display",
            "html" : html,
            "note" : note,
            "total" : int(data['total'] * 100),
            "reference" : data['reference']
        }

    logger.info(display)

    # Send cloud push message
    logger.debug(note)
    to = [active.token,]

    PushyAPI.sendPushNotification(display, to, None)


@staff_member_required
def onsiteSelectTerminal(request):
    selected = request.POST.get('terminal', None)
    try:
        active = Firebase.objects.get(id=selected)
    except Firebase.DoesNotExist:
        return JsonResponse({'success' : False, 'reason' : 'Terminal does not exist'}, status=404)
    request.session['terminal'] = selected
    return JsonResponse({'success' : True})

#@staff_member_required
def assignBadgeNumber(request):
    badge_id = request.GET.get('id');
    badge_number = request.GET.get('number')
    badge_name = request.GET.get('badge', None)
    badge = None

    if badge_name is not None:
        try:
            badge = Badge.objects.filter(badgeName__icontains=badge_name, event__name="Furthemore 2018").first()

        except:
            return JsonResponse({'success' : False, 'reason' : 'Badge name search returned no results'})
    else:
        if badge_id is None or badge_number is None:
            return JsonResponse({'success' : False, 'reason' : 'id and number are required parameters'}, status=400)

    try:
        badge_number = int(badge_number)
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Badge number must be an integer'}, status=400)


    if badge is None:
        try:
            badge = Badge.objects.get(id=int(badge_id))
        except Badge.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Badge ID specified does not exist'}, status=404)
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Badge ID must be an integer'}, status=400)

    try:
        badge.badgeNumber = badge_number
        badge.save()
    except Exception as e:
        return JsonResponse({'success' : False, 'message' : 'Error while saving badge number'}, status=500)

    return JsonResponse({'success' : True})

@staff_member_required
def onsitePrintBadges(request):
    badge_list = request.GET.getlist('id')
    con = printing.Main(local=True)
    tags = []

    for badge_id in badge_list:
        try:
            badge = Badge.objects.get(id=badge_id)
        except Badge.DoesNotExist:
            return JsonResponse({'success' : False, 'message' : 'Badge id {0} does not exist'.format(badge_id)}, status=404)

        if badge.badgeNumber is None:
            badgeNumber = ''
        else:
            badgeNumber = '{:04}'.format(badge.badgeNumber)

        tags.append({
            'name' : badge.badgeName,
            'number' : badgeNumber,
            'level' : str(badge.effectiveLevel()),
            'title' : ''
        })
        badge.printed = True
        badge.save()

    con.nametags(tags, theme='apis')
    pdf_path = con.pdf.split('/')[-1]

    file_url = reverse(printNametag) + '?file={0}'.format(pdf_path)

    return JsonResponse({
        'success' : True,
        'file' : pdf_path,
        'next' : request.get_full_path(),
        'url' : file_url
    })


#@staff_member_required
def onsiteSignature(request):
    context = {}
    return render(request, 'registration/signature.html', context)


###################################
# Attendees

def checkBanList(firstName, lastName, email):
    banCheck = BanList.objects.filter(firstName=firstName, lastName=lastName, email=email)
    if banCheck.count() > 0:
        return True
    return False

def upgrade(request, guid):
    context = {'token': guid}
    return render(request, 'registration/attendee-locate.html', context)

def infoUpgrade(request):
  try:
    postData = json.loads(request.body)
    email = postData['email']
    token = postData['token']

    evt = postData['event']
    event = Event.objects.get(name=evt)

    badge = Badge.objects.get(registrationToken=token)
    if not badge:
      return HttpResponseServerError("No Record Found")

    attendee = badge.attendee
    if attendee.email.lower() != email.lower():
      return HttpResponseServerError("No Record Found")

    request.session['attendee_id'] = attendee.id
    request.session['badge_id'] = badge.id
    return JsonResponse({'success': True, 'message':'ATTENDEE'})
  except Exception as e:
    logger.exception("Error in starting upgrade.")
    return HttpResponseServerError(str(e))

def findUpgrade(request):
    context = {'attendee': None}
    try:
      attId = request.session['attendee_id']
      badgeId = request.session['badge_id']
    except Exception as e:
      return render(request, 'registration/attendee-upgrade.html', context)

    attendee = Attendee.objects.get(id=attId)
    if attendee:
        badge = Badge.objects.get(id=badgeId)
        attendee_dict = model_to_dict(attendee)
        badge_dict = {'id': badge.id}
        lvl = badge.effectiveLevel()
        existingOIs = badge.getOrderItems()
        lvl_dict = {'basePrice': lvl.basePrice, 'options': getOptionsDict(existingOIs)}
        context = {'attendee': attendee, 'badge': badge,
                   'jsonAttendee': json.dumps(attendee_dict, default=handler),
                   'jsonBadge': json.dumps(badge_dict, default=handler),
                   'jsonLevel': json.dumps(lvl_dict, default=handler)}
    return render(request, 'registration/attendee-upgrade.html', context)

def addUpgrade(request):
    postData = json.loads(request.body)
    pda = postData['attendee']
    pdp = postData['priceLevel']
    pdd = postData['badge']
    evt = postData['event']
    event = Event.objects.get(name=evt)

    if 'attendee_id' not in request.session:
        return HttpResponseServerError("Session expired")

    ## Update Attendee info
    attendee = Attendee.objects.get(id=pda['id'])
    if not attendee:
        return HttpResponseServerError("Attendee id not found")

    badge = Badge.objects.get(id=pdd['id'])
    priceLevel = PriceLevel.objects.get(id=int(pdp['id']))

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy="WEB")
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
        badgeId = request.session.get('badge_id', -1)
        if attendeeId == -1 or badgeId == -1:
            context = {'orderItems': [], 'total': 0, 'discount': {}}
            request.session.flush()
        else:
            badge = Badge.objects.get(id=badgeId)
            attendee = Attendee.objects.get(id=attendeeId)
            lvl = badge.effectiveLevel()
            lvl_dict = {'basePrice': lvl.basePrice}
            orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
            total = getTotal(orderItems)
            context = {'orderItems': orderItems, 'total': total, 'attendee': attendee, 'prevLevel': lvl_dict}
    return render(request, 'registration/upgrade-checkout.html', context)

def doneUpgrade(request):
    context = {}
    return render(request, 'registration/upgrade-done.html', context)

def checkoutUpgrade(request):
  try:
    sessionItems = request.session.get('order_items', [])
    orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
    if 'attendee_id' not in request.session:
        return HttpResponseServerError("Session expired")

    attendee = Attendee.objects.get(id=request.session.get('attendee_id'))
    postData = json.loads(request.body)
    event = Event.objects.get(default=True)

    subtotal = getTotal(orderItems)

    if subtotal == 0:
        status, message, order = doZeroCheckout(attendee, discount, orderItems)
        if not status:
            return JsonResponse({'success': False, 'message': message})

        request.session.flush()
        try:
            sendUpgradePaymentEmail(attendee, order)
        except Exception as e:
            logger.exception("Error sending UpgradePaymentEmail - zero sum.")
            return JsonResponse({'success': False, 'message': "Your upgrade payment succeeded but we may have been unable to send you a confirmation email. If you do not receive one within the next hour, please contact registration@furthemore.org to get your confirmation number."})
        return JsonResponse({'success': True})

    porg = Decimal(postData["orgDonation"].strip() or 0.00)
    pcharity = Decimal(postData["charityDonation"].strip() or 0.00)
    if porg < 0:
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity

    pbill = postData['billingData']
    ip = get_client_ip(request)
    status, message, order = doCheckout(pbill, total, None, orderItems, porg, pcharity, ip)

    if status:
        request.session.flush()
        try:
            sendUpgradePaymentEmail(attendee, order)
        except Exception as e:
            logger.exception("Error sending UpgradePaymentEmail.")
            return JsonResponse({'success': False, 'message': "Your upgrade payment succeeded but we may have been unable to send you a confirmation email. If you do not receive one within the next hour, please contact registration@furthemore.org to get your confirmation number."})
        return JsonResponse({'success': True})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': response})

  except Exception as e:
    logger.exception("Error in attendee upgrade.")
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

        hasMinors = False
        for item in orderItems:
            if item.badge.isMinor():
              hasMinors = True
              break

        context = {'orderItems': orderItems, 'total': total, 'discount': discount, 'hasMinors': hasMinors}
    return render(request, 'registration/checkout.html', context)


def addToCart(request):
    postData = json.loads(request.body)
    #create attendee from request post
    pda = postData['attendee']
    pdp = postData['priceLevel']
    evt = postData['event']

    banCheck = checkBanList(pda['firstName'], pda['lastName'], pda['email'])
    if banCheck:
        logger.exception("***ban list registration attempt***")
        return JsonResponse({'success': False, 'message': "We are sorry, but you are unable to register for " + evt + ". If you have any questions, or would like further information or assistance, please contact Registration at registration@furthemore.org."})

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda['birthdate'], '%Y-%m-%d' ))

    event = Event.objects.get(name=evt)

    attendee = Attendee(firstName=pda['firstName'], lastName=pda['lastName'], address1=pda['address1'], address2=pda['address2'],
                        city=pda['city'], state=pda['state'], country=pda['country'], postalCode=pda['postal'],
                        phone=pda['phone'], email=pda['email'], birthdate=birthdate,
                        emailsOk=bool(pda['emailsOk']), volunteerContact=len(pda['volDepts']) > 0, volunteerDepts=pda['volDepts'],
                        surveyOk=bool(pda['surveyOk']), aslRequest=bool(pda['asl']))
    attendee.save()

    badge = Badge(badgeName=pda['badgeName'], event=event, attendee=attendee)
    badge.save()

    priceLevel = PriceLevel.objects.get(id=int(pdp['id']))

    via = "WEB"
    if postData['attendee'].get('onsite', False):
        via = "ONSITE"

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy=via)
    orderItem.save()

    for option in pdp['options']:
        plOption = PriceLevelOption.objects.get(id=int(option['id']))
        if plOption.optionExtraType == 'int' and option['value'] == '':
            attendeeOption = AttendeeOptions(option=plOption, orderItem=orderItem, optionValue='0')
        else:
            attendeeOption = AttendeeOptions(option=plOption, orderItem=orderItem, optionValue=option['value'])
        attendeeOption.save()

    #add attendee to session order
    orderItems = request.session.get('order_items', [])
    orderItems.append(orderItem.id)
    request.session['order_items'] = orderItems
    return JsonResponse({'success': True})


def removeFromCart(request):
    postData = json.loads(request.body)
    id = postData['id']
    #locate attendee in session order
    order = request.session.get('order_items', [])
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

    if subtotal == 0:
        att = orderItems[0].badge.attendee
        status, message, order = doZeroCheckout(att, discount, orderItems)
        if not status:
            return JsonResponse({'success': False, 'message': message})

        request.session.flush()
        try:
            sendRegistrationEmail(order, att.email)
        except Exception as e:
            logger.exception("Error sending RegistrationEmail - zero sum.")
            return JsonResponse({'success': False, 'message': "Your payment succeeded but we may have been unable to send you a confirmation email. If you do not receive one within the next hour, please contact registration@furthemore.org to get your confirmation number."})
        return JsonResponse({'success': True})

    porg = Decimal(postData["orgDonation"].strip() or 0.00)
    pcharity = Decimal(postData["charityDonation"].strip() or 0.00)
    pbill = postData["billingData"]

    if porg < 0:
        porg = 0
    if pcharity < 0:
        pcharity = 0

    total = subtotal + porg + pcharity
    ip = get_client_ip(request)

    onsite = postData["onsite"]
    if onsite:
        att = orderItems[0].badge.attendee
        billingData = {
            'cc_firstname' : att.firstName,
            'cc_lastname' : att.lastName,
            'email' : att.email,
            'address1' : att.address1,
            'address2' : att.address2,
            'city' : att.city,
            'state' : att.state,
            'country' : att.country,
            'postal' : att.postalCode
        }
        reference = getConfirmationToken()
        while Order.objects.filter(reference=reference).count() > 0:
            reference = getConfirmationToken()

        order = Order(total=Decimal(total), reference=reference, discount=discount,
                      orgDonation=porg, charityDonation=pcharity, billingType=Order.UNPAID,
                      billingName=billingData['cc_firstname'] + " " + billingData['cc_lastname'],
                      billingAddress1=billingData['address1'], billingAddress2=billingData['address2'],
                      billingCity=billingData['city'], billingState=billingData['state'], billingCountry=billingData['country'],
                      billingPostal=billingData['postal'], billingEmail=billingData['email'])
        order.status = "Onsite Pending"
        order.save()

        for oitem in orderItems:
            oitem.order = order
            oitem.save()
        if discount:
            discount.used = discount.used + 1
            discount.save()

        status = True
        message = "Onsite success"
    else:
        status, message, order = doCheckout(pbill, total, discount, orderItems, porg, pcharity, ip)

    if status:
        request.session.flush()
        try:
            sendRegistrationEmail(order, order.billingEmail)
        except Exception as e:
            logger.exception("Error sending RegistrationEmail.")
            return JsonResponse({'success': False, 'message': "Your payment succeeded but we may have been unable to send you a confirmation email. If you do not receive one within the next hour, please contact registration@furthemore.org to get your confirmation number."})
        return JsonResponse({'success': True})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': message})


def cartDone(request):
    event = Event.objects.get(default=True)
    context = {'event': event}
    return render(request, 'registration/done.html', context)

###################################
# Staff only access

@staff_member_required
def basicBadges(request):
    badges = Badge.objects.all()
    staff = Staff.objects.all()

    bdata = [{'badgeName': badge.badgeName, 'level': badge.effectiveLevel().name, 'assoc':badge.abandoned(),
              'firstName': badge.attendee.firstName.lower(), 'lastName': badge.attendee.lastName.lower(),
              'printed': badge.printed, 'discount': badge.getDiscount(),
              'assoc': badge.abandoned(), 'orderItems': getOptionsDict(badge.orderitem_set.all()) }
             for badge in badges if badge.effectiveLevel() != None and badge.event.name == "Furthemore 2018"]

    staffdata = [{'firstName': s.attendee.firstName.lower(), 'lastName':s.attendee.lastName.lower(),
                  'title': s.title, 'id': s.id}
                for s in staff if s.event.name == "Furthemore 2018"]

    for staff in staffdata:
        sbadge = Staff.objects.get(id=staff['id']).getBadge()
        if sbadge:
            staff['badgeName'] = sbadge.badgeName
            if sbadge.effectiveLevel():
                staff['level'] = sbadge.effectiveLevel().name
            else:
                staff['level'] = "none"
            staff['assoc'] = sbadge.abandoned()
            staff['orderItems'] = getOptionsDict(sbadge.orderitem_set.all())

    sdata = sorted(bdata, key=lambda x:(x['level'],x['lastName']))
    ssdata = sorted(staffdata, key=lambda x:x['lastName'])

    dealers = [att for att in sdata if att['assoc'] == 'Dealer']
    staff = [att for att in ssdata]
    attendees = [att for att in sdata if att['assoc'] != 'Staff' ]
    return render(request, 'registration/utility/badgelist.html', {'attendees': attendees, 'dealers': dealers, 'staff': staff})

@staff_member_required
def vipBadges(request):
    badges = Badge.objects.all()
    vipLevels = ('God-mode','God-Mode','Player','Raven God','Elite Sponsor','Super Sponsor')

    bdata = [{'badge': badge, 'orderItems': getOptionsDict(badge.orderitem_set.all()),
              'level': badge.effectiveLevel().name, 'assoc': badge.abandoned}
             for badge in badges if badge.effectiveLevel() != None and badge.effectiveLevel() != 'Unpaid' and
               badge.effectiveLevel().name in vipLevels and badge.abandoned != 'Staff']

    events = Event.objects.all()
    events.reverse()

    return render(request, 'registration/utility/holidaylist.html', {'badges': bdata, 'events': events})



###################################
# Printing

def printNametag(request):
    context = {
        'file' : request.GET.get('file', None),
        'next' : request.GET.get('next', None)
    }
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
    orderDict = []
    for oi in orderItems:
        aos = oi.getOptions()
        for ao in aos:
            if ao.optionValue == 0 or ao.optionValue == None or ao.optionValue == "" or ao.optionValue == False: pass

            orderDict.append({'name': ao.option.optionName, 'value': ao.optionValue,
                              'id': ao.option.id, 'type': ao.option.optionExtraType,
                              'description': ao.option.description})

    return orderDict

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

def getPriceLevelList(levels):
    data = [ {
        'name': level.name,
        'id':level.id,
        'base_price': level.basePrice.__str__(),
        'description': level.description,
        'options': [{
            'name': option.optionName,
            'value': option.optionPrice,
            'id': option.id,
            'required': option.required,
            'active': option.active,
            'type': option.optionExtraType,
            'description': option.description,
            'list': option.getList()
            } for option in level.priceLevelOptions.order_by('rank', 'optionPrice').all() ]
          } for level in levels ]
    return data

def getMinorPriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=False, startDate__lte=now, endDate__gte=now, name__icontains='minor').order_by('basePrice')
    data = getPriceLevelList(levels)
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def getAccompaniedPriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=False, startDate__lte=now, endDate__gte=now, name__icontains='accompanied').order_by('basePrice')
    data = getPriceLevelList(levels)
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def getFreePriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=False, startDate__lte=now, endDate__gte=now, name__icontains='free')
    data = getPriceLevelList(levels)
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')


def getPriceLevels(request):
    dealer = request.session.get('dealer_id', -1)
    staff = request.session.get('staff_id', -1)
    attendee = request.session.get('attendee_id', -1)
    #hide any irrelevant price levels if something in session
    att = None
    if dealer > 0:
        deal = Dealer.objects.get(id=dealer)
        att = deal.attendee
        event = deal.event
        badge = Badge.objects.filter(attendee=att,event=event).last()
    if staff > 0:
        sta = Staff.objects.get(id=staff)
        att = sta.attendee
        event = sta.event
        badge = Badge.objects.filter(attendee=att,event=event).last()
    if attendee > 0:
        att = Attendee.objects.get(id=attendee)
        badge = Badge.objects.filter(attendee=att).last()

    now = timezone.now()
    levels = PriceLevel.objects.filter(public=True, startDate__lte=now, endDate__gte=now).order_by('basePrice')
    if att and badge and badge.effectiveLevel():
        levels = levels.exclude(basePrice__lt=badge.effectiveLevel().basePrice)
    data = getPriceLevelList(levels)
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def getAdultPriceLevels(request):
    dealer = request.session.get('dealer_id', -1)
    staff = request.session.get('staff_id', -1)
    attendee = request.session.get('attendee_id', -1)
    #hide any irrelevant price levels if something in session
    att = None
    if dealer > 0:
        deal = Dealer.objects.get(id=dealer)
        att = deal.attendee
        event = deal.event
        badge = Badge.objects.filter(attendee=att,event=event).last()
    if staff > 0:
        sta = Staff.objects.get(id=staff)
        att = sta.attendee
        event = sta.event
        badge = Badge.objects.filter(attendee=att,event=event).last()
    if attendee > 0:
        att = Attendee.objects.get(id=attendee)
        badge = Badge.objects.filter(attendee=att).last()

    now = timezone.now()
    levels = PriceLevel.objects.filter(public=True, isMinor=False, startDate__lte=now, endDate__gte=now).order_by('basePrice')
    if att and badge and badge.effectiveLevel():
        levels = levels.exclude(basePrice__lt=badge.effectiveLevel().basePrice)
    data = getPriceLevelList(levels)
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')    

def getShirtSizes(request):
    sizes = ShirtSizes.objects.all()
    data = [{'name': size.name, 'id': size.id} for size in sizes]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getTableSizes(request):
    event = Event.objects.get(default=True)
    sizes = TableSize.objects.filter(event=event)
    data = [{'name': size.name, 'id': size.id, 'description': size.description, 'chairMin': size.chairMin, 'chairMax': size.chairMax, 'tableMin': size.tableMin, 'tableMax': size.tableMax, 'partnerMin': size.partnerMin, 'partnerMax': size.partnerMax, 'basePrice': str(size.basePrice)} for size in sizes]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getSessionAddresses(request):
    sessionItems = request.session.get('order_items', [])
    if not sessionItems:
        data = {}
    else:
        orderItems = OrderItem.objects.filter(id__in=sessionItems)
        data = [{'id': oi.badge.attendee.id, 'fname': oi.badge.attendee.firstName,
                 'lname': oi.badge.attendee.lastName, 'email': oi.badge.attendee.email,
                 'address1': oi.badge.attendee.address1, 'address2': oi.badge.attendee.address2,
                 'city': oi.badge.attendee.city, 'state': oi.badge.attendee.state, 'country': oi.badge.attendee.country,
                 'postalCode': oi.badge.attendee.postalCode} for oi in orderItems]
        context = {'addresses': data}
    return HttpResponse(json.dumps(data), content_type='application/json')

@csrf_exempt
def completeSquareTransaction(request):
    key = request.GET.get('key', '')
    reference = request.GET.get('reference', None)
    clientTransactionId = request.GET.get('clientTransactionId', None)
    serverTransactionId = request.GET.get('serverTransactionId', None)

    if key != settings.REGISTER_KEY:
        return JsonResponse({'success' : False, 'reason' : 'Incorrect API key'}, status=401)

    if reference is None or clientTransactionId is None:
        return JsonResponse({'success' : False, 'reason' : 'Reference and clientTransactionId are required parameters'}, status=400)

    # Things we need:
    #   orderID or reference (passed to square by metadata)
    # Square returns:
    #   clientTransactionId (offline payments)
    #   serverTransactionId (online payments)

    try:
        order = Order.objects.get(reference=reference)
    except Order.DoesNotExist:
        return JsonResponse({'success' : False, 'reason' : 'No order matching the reference specified exists'}, status=404)

    order.billingType = Order.CREDIT
    order.status = "Complete"
    order.settledDate = datetime.now()
    order.notes = json.dumps({
        'clientTransactionId' : clientTransactionId,
        'serverTransactionId' : serverTransactionId
    })
    order.save()

    return JsonResponse({'success' : True})


@csrf_exempt
def firebaseRegister(request):
    key = request.GET.get('key', '')
    if key != settings.REGISTER_KEY:
        return JsonResponse({'success' : False, 'reason' : 'Incorrect API key'}, status=401)

    token = request.GET.get('token', None)
    name = request.GET.get('name', None)
    if token is None or name is None:
        return JsonResponse({'success' : False, 'reason' : 'Must specify token and name parameter'}, status=400)

    # Upsert if a new token with an existing name tries to register
    try:
        old_terminal = Firebase.objects.get(name=name)
        old_terminal.token = token
        old_terminal.save()
        return JsonResponse({'success' : True, 'updated' : True})
    except Firebase.DoesNotExist:
        pass
    except Exception as e:
        return JsonResponse({'success' : False, 'reason' : 'Failed while attempting to update existing name entry'}, status=500)

    # Upsert if a new name with an existing token tries to register
    try:
        old_terminal = Firebase.objects.get(token=token)
        old_terminal.name = name
        old_terminal.save()
        return JsonResponse({'success' : True, 'updated' : True})
    except Firebase.DoesNotExist:
        pass
    except Exception as e:
        return JsonResponse({'success' : False, 'reason' : 'Failed while attempting to update existing token entry'}, status=500)

    try:
        terminal = Firebase(token=token, name=name)
        terminal.save()
    except Exception as e:
        logger.exception(e)
        logger.error("Error while saving Firebase token to database")
        return JsonResponse({'success' : False, 'reason' : 'Error while saving to database'}, status=500)

    return JsonResponse({'success' : True, 'updated' : False})

@csrf_exempt
def firebaseLookup(request):
    # Returns the common name stored for a given firebase token
    # (So client can notify server if either changes)
    token = request.GET.get('token', None)
    if token is None:
        return JsonResponse({'success' : False, 'reason' : 'Must specify token parameter'}, status=400)

    try:
        terminal = Firebase.objects.get(token=token)
        return JsonResponse({'success' : True, 'name' : terminal.name, 'closed' : terminal.closed})
    except Firebase.DoesNotExist:
        return JsonResponse({'success' : False, 'reason' : 'No such token registered'}, status=404)



##################################
# Not Endpoints

def getConfirmationToken():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase+string.digits) for _ in range(6))

def deleteOrderItem(id):
    orderItems = OrderItem.objects.filter(id=id)
    if orderItems.count() == 0:
      return
    orderItem = orderItems.first()
    orderItem.badge.attendee.delete()
    orderItem.badge.delete()
    orderItem.delete()

def handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return str(obj)
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

