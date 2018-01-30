from django.contrib.admin.views.decorators import staff_member_required
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
    event = Event.objects.get(name__icontains="2018")
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
        badges = Badge.objects.filter(attendee=staff.attendee,event=staff.event)
        lvl_dict = {}
        badge = {}
        if badges.count() > 0:
            badge = badges[0]
            if badge.effectiveLevel():
                lvl_dict["basePrice"] = badge.effectiveLevel().basePrice

        context = {'staff': staff, 'jsonStaff': json.dumps(staff_dict, default=handler),
                   'jsonAttendee': json.dumps(attendee_dict, default=handler),
                   'jsonLevel': json.dumps(lvl_dict, default=handler),
                   'badge': badge}
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
    pds = postData['staff']

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
        return JsonResponse({'success': False, 'message': 'Staff not saved: ' + str(e)})

    event = staff.event

    badges = Badge.objects.filter(attendee=attendee,event=event)
    if badges.count() == 0:
        badge = Badge(attendee=attendee,event=event,badgeName=pda['badgeName'])
    else:
        badge = badges[0]
        badge.badgeName = pda['badgeName']
    try:
        badge.save()
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Badge not saved: ' + str(e)})

    priceLevel = PriceLevel.objects.get(id=int(pdp['id']))

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy="WEB")
    orderItem.save()

    for option in pdp['options']:
        plOption = PriceLevelOption.objects.get(id=int(option['id']))
        attendeeOption = AttendeeOptions(option=plOption, orderItem=orderItem, optionValue=option['value'])
        attendeeOption.save()

    #add to session order
    orderItems = request.session.get('order_items', [])
    orderItems.append(orderItem.id)
    request.session['order_items'] = orderItems
    request.session["discount"] = "StaffDiscount"

    return JsonResponse({'success': True})


def getStaffTotal(orderItems, discount, staff):
    badge = Badge.objects.get(attendee=staff.attendee,event=staff.event)
    if badge.effectiveLevel():
        discount = None
    subTotal = getTotal(orderItems, discount)
    alreadyPaid = badge.paidTotal()
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

    discount = Discount.objects.get(codeName="StaffDiscount")
    staff = Staff.objects.get(id=staffId)
    subtotal = getStaffTotal(orderItems, discount, staff)

    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    email = ''
    total = 0
    if subtotal == 0:
      att = staff.attendee
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

      discount.used = discount.used + 1
      discount.save()
      sendStaffRegistrationEmail(order.id, email)
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

    status, response = chargePayment(order.id, pbill, get_client_ip(request))

    if status:
        for oitem in orderItems:
            oitem.order = order
            oitem.save()
        order.status = 'Paid'
        order.save()
        request.session.flush()
        discount.used = discount.used + 1
        discount.save()
        sendStaffRegistrationEmail(order.id, email)
        return JsonResponse({'success': True})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': response})



###################################
# Dealers

def dealers(request, guid):
    context = {'token': guid}
    return render(request, 'registration/dealer-locate.html', context)

def dealerAsst(request, guid):
    context = {'token': guid}
    return render(request, 'registration/dealerasst-locate.html', context)

def newDealer(request):
    event = Event.objects.last()
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
        badge = Badge.objects.filter(attendee=dealer.attendee, event=dealer.event).last()
        dealer_dict = model_to_dict(dealer)
        attendee_dict = model_to_dict(dealer.attendee)
        badge_dict = model_to_dict(badge)
        table_dict = model_to_dict(dealer.tableSize)
        if badge.effectiveLevel():
            lvl_dict = model_to_dict(badge.effectiveLevel())
        else:
            lvl_dict = {}
        context = {'dealer': dealer, 'badge': badge,
                   'jsonDealer': json.dumps(dealer_dict, default=handler),
                   'jsonTable': json.dumps(table_dict, default=handler),
                   'jsonAttendee': json.dumps(attendee_dict, default=handler),
                   'jsonBadge': json.dumps(badge_dict, default=handler),
                   'jsonLevel': json.dumps(lvl_dict, default=handler)}
    return render(request, 'registration/dealer-payment.html', context)

def getDealerTotal(orderItems, discount, dealer):
    subTotal = getTotal(orderItems, discount)
    partnerCount = dealer.getPartnerCount()
    partnerBreakfast = 0
    if partnerCount > 0 and dealer.asstBreakfast:
      partnerBreakfast = 60*partnerCount
    wifi = 0
    if dealer.needWifi:
        wifi = 50
    paidTotal = dealer.paidTotal()
    total = subTotal + 45*partnerCount + partnerBreakfast + dealer.tableSize.basePrice + wifi - dealer.discount - paidTotal
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

    reference = getConfirmationToken()
    while Order.objects.filter(reference=reference).count() > 0:
        reference = getConfirmationToken()

    partners = partnerCount - originalPartnerCount
    total = Decimal(45*partners)
    if pbill['breakfast']:
        total = total + Decimal(60*partners)

    order = Order(total=total, reference=reference, discount=None,
                  orgDonation=0, charityDonation=0, billingName=pbill['cc_firstname'] + " " + pbill['cc_lastname'],
                  billingAddress1=pbill['address1'], billingAddress2=pbill['address2'],
                  billingCity=pbill['city'], billingState=pbill['state'], billingCountry=pbill['country'],
                  billingPostal=pbill['postal'], billingEmail=pbill['email'])
    order.save()

    orderItem.order = order
    orderItem.save()

    status, response = chargePayment(order.id, pbill, get_client_ip(request))

    if status:
        orderItem.order = order
        orderItem.save()
        order.status = "Paid"
        order.save()
        request.session.flush()
        try:
            sendDealerAsstEmail(dealer.id)
        except Exception as e:
            return JsonResponse({'success': False, 'message': "Your payment succeeded but we may have been unable to send you a confirmation email. If you do not receive one within the next hour, please contact marketplace@furthemore.org to get your confirmation number."})
        return JsonResponse({'success': True})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': response})


def addDealer(request):
    postData = json.loads(request.body)
    pda = postData['attendee']
    pdd = postData['dealer']
    pdp = postData['priceLevel']
    evt = postData['event']
    event = Event.objects.get(name=evt)

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
    dealer.asstBreakfast=pdd['asstbreakfast']
    dealer.event = event

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

    try:
        attendee.save()
    except Exception as e:
        return HttpResponseServerError(str(e))


    badge = Badge.objects.get(attendee=attendee,event=event)
    badge.badgeName=pda['badgeName']

    try:
        badge.save()
    except Exception as e:
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


    status, response = chargePayment(order.id, pbill, get_client_ip(request))

    if status:
        sendDealerPaymentEmail(dealer, order)
        orderItem.order = order
        orderItem.save()
        order.status = "Paid"
        order.save()
        request.session.flush()
        return JsonResponse({'success': True})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': response})
  except Exception as e:
    return HttpResponseServerError(str(e))


def addNewDealer(request):
  try:
    postData = json.loads(request.body)
    #create attendee from request post
    pda = postData['attendee']
    pdd = postData['dealer']
    evt = postData['event']

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda['birthdate'], '%m/%d/%Y' ))
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
    dealer = Dealer(attendee=attendee, event=event, businessName=pdd['businessName'],
                    website=pdd['website'], description=pdd['description'], license=pdd['license'], needPower=pdd['power'],
                    needWifi=pdd['wifi'], wallSpace=pdd['wall'], nearTo=pdd['near'], farFrom=pdd['far'], tableSize=tablesize,
                    chairs=pdd['chairs'], reception=pdd['reception'], artShow=pdd['artShow'], charityRaffle=pdd['charityRaffle'],
                    breakfast=pdd['breakfast'], willSwitch=pdd['switch'], tables=pdd['tables'],
                    agreeToRules=pdd['agreeToRules'], partners=pdd['partners'], buttonOffer=pdd['buttonOffer'], asstBreakfast=pdd['asstbreakfast']
    )
    dealer.save()
    sendDealerApplicationEmail(dealer.id)
    return JsonResponse({'success': True})
  except Exception as e:
    return HttpResponseServerError(str(e))


###################################
# Attendees - Onsite

def onsite(request):
    # FIXME: need mechanism for getting the current event, not just the first row in the db
    event = Event.objects.get(name__icontains="2018")
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
        badge_dict = model_to_dict(badge)
        lvl_dict = model_to_dict(badge.effectiveLevel())
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

    status, response = chargePayment(order.id, pbill, get_client_ip(request))

    if status:
        sendUpgradePaymentEmail(attendee, order)
        orderItem.order = order
        orderItem.save()
        request.session.flush()
        return JsonResponse({'success': True})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': response})


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
    evt = postData['event']

    banCheck = checkBanList(pda['firstName'], pda['lastName'], pda['email'])
    if banCheck:
        return JsonResponse({'success': False, 'message': "We are sorry, but you are unable to register for Furthemore 2018. If you have any questions, or would like further information or assistance, please contact Registration at registration@furthemore.org."})

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda['birthdate'], '%m/%d/%Y' ))

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

    orderItem = OrderItem(badge=badge, priceLevel=priceLevel, enteredBy="WEB")
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
        att = orderItems[0].badge.attendee
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
        sendRegistrationEmail(order, att.email)
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
        att = orderItems[0].badge.attendee
        order = Order(total=0, reference=reference, discount=discount,
                  orgDonation=0, charityDonation=0, billingName=att.firstName + " " + att.lastName,
                  billingAddress1=att.address1, billingAddress2=att.address2,
                  billingCity=att.city, billingState=att.state, billingCountry=att.country,
                  billingPostal=att.postalCode, status="Onsite Pending", billingEmail=att.email)
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

    status, response = chargePayment(order.id, pbill, get_client_ip(request))

    if status:
        for oitem in orderItems:
            oitem.order = order
            oitem.save()
            order.status = "Paid"
            order.save()
        if discount:
            discount.used = discount.used + 1
            discount.save()
        sendRegistrationEmail(order, pbill['email'])
        request.session.flush()
        return JsonResponse({'success': True})
    else:
        order.delete()
        return JsonResponse({'success': False, 'message': response})


def cartDone(request):
    context = {}
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

    #data = [{'firstName': att.firstName.lower(), 'lastName': att.lastName.lower(), 'badgeName': att.badgeName,
    #         'badgeNumber': att.badgeNumber, 'level': att.effectiveLevel().name, 'printed': att.printed,
    #         'assoc': att.abandoned(), 'orderItems':getOptionsDict(att.orderitem_set.all()),
    #         'discount': att.getDiscount()} for att in attendees if att.effectiveLevel() != None]

    staffdata = [{'firstName': s.attendee.firstName.lower(), 'lastName':s.attendee.lastName.lower(),
                  'title': s.title, 'id': s.id}
                for s in staff if s.event.name == "Furthemore 2018"]

    for staff in staffdata:
        sbadge = Staff.objects.get(id=staff['id']).getBadge()
        if sbadge:
            staff['badgeName'] = sbadge.badgeName
            staff['level'] = sbadge.effectiveLevel().name
            staff['assoc'] = sbadge.abandoned()
            staff['orderItems'] = getOptionsDict(sbadge.orderitem_set.all())

    sdata = sorted(bdata, key=lambda x:(x['level'],x['lastName']))
    ssdata = sorted(staffdata, key=lambda x:x['lastName'])

    dealers = [att for att in sdata if att['assoc'] == 'Dealer']
    staff = [att for att in ssdata]
    attendees = [att for att in sdata if att['assoc'] != 'Staff' ]
    return render(request, 'registration/utility/badgelist.html', {'attendees': attendees, 'dealers': dealers, 'staff': staff})

@staff_member_required
def holidayBadges(request):
    badges = Badge.objects.all()

    bdata = [{'badgeName': badge.badgeName, 'level': badge.effectiveLevel().name, 'assoc':badge.abandoned(),
              'firstName': badge.attendee.firstName.lower(), 'lastName': badge.attendee.lastName.lower(),
              'address': badge.attendee.address1 + " " + badge.attendee.address2,
              'city': badge.attendee.city, 'state': badge.attendee.state, 'postal': badge.attendee.postalCode,
              'country': badge.attendee.country, 'event': badge.event.name }
             for badge in badges if badge.effectiveLevel() != None]

    sdata = sorted(bdata, key=lambda x:(x['event'],x['level'],x['lastName']))
    attendees = [att for att in sdata if att['assoc'] != 'Staff' and att['level'] in ('God-mode','God-Mode','Player','Raven God', 'Elite Sponsor') ]
    return render(request, 'registration/utility/holidaylist.html', {'attendees': attendees})



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
            'list': option.getList()
            } for option in level.priceLevelOptions.order_by('optionPrice').all() ]
          } for level in levels ]
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def getAccompaniedPriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=False, startDate__lte=now, endDate__gte=now, name__icontains='accompanied').order_by('basePrice')
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
            'list': option.getList()
            } for option in level.priceLevelOptions.order_by('optionPrice').all() ]
          } for level in levels ]
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def getFreePriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=False, startDate__lte=now, endDate__gte=now, name__icontains='free')
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
            'list': option.getList()
            } for option in level.priceLevelOptions.order_by('optionPrice').all() ]
          } for level in levels ]
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
    data = [{'name': level.name, 'id':level.id,  'base_price': level.basePrice.__str__(), 'description': level.description,'options': [{'name': option.optionName, 'value': option.optionPrice, 'id': option.id, 'required': option.required, 'active': option.active, 'type': option.optionExtraType, "list": option.getList() } for option in level.priceLevelOptions.order_by('optionPrice').all() ]} for level in levels]
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def getShirtSizes(request):
    sizes = ShirtSizes.objects.all()
    data = [{'name': size.name, 'id': size.id} for size in sizes]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getTableSizes(request):
    event = Event.objects.last()
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


def handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return str(obj)
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

