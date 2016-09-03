from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.utils import timezone
from datetime import datetime
from decimal import *
import json
import random
import string

from .models import *
from .payments import chargePayment

# Create your views here.

def index(request):
    context = {}
    return render(request, 'registration/registration-form.html', context)


###################################
# Payments

def getCart(request):
    sessionItems = request.session.get('order_items', [])
    if not sessionItems:
        context = {'orderItems': [], 'total': 0}
    else:
        orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
        total = getTotal(orderItems)
        context = {'orderItems': orderItems, 'total': total}
    return render(request, 'registration/checkout.html', context)

def addToCart(request):
    #create attendee from request post
    postData = json.loads(request.body)
    pda = postData['attendee']
    pdp = postData['priceLevel']

    tz = timezone.get_current_timezone()
    birthdate = tz.localize(datetime.strptime(pda['birthdate'], '%m/%d/%Y' ))
    #TODO: get correct event
    event = Event.objects.first()

    attendee = Attendee(firstName=pda['firstName'], lastName=pda['lastName'], address1=pda['address1'], address2=pda['address2'],
                        city=pda['city'], state=pda['state'], country=pda['country'], postalCode=pda['postal'],
                        phone=pda['phone'], email=pda['email'], birthdate=birthdate,
                        badgeName=pda['badgeName'], emailsOk=pda['emailsOk'], volunteerContact=pda['volunteer'], volunteerDepts=pda['volDepts'],
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

    #add attendee to session order
    orderItems = request.session.get('order_items', [])
    orderItems.append(orderItem.id)
    request.session['order_items'] = orderItems
    return HttpResponse("Success")

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
        ccode = getConfirmationCode()

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
    depts = Department.objects.filter(volunteerListOk=True)
    data = [{'name': item.name, 'id': item.id} for item in depts]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getPriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=True, startDate__lte=now, endDate__gte=now)
    data = [{'name': level.name, 'base_price': level.basePrice.__str__(), 'description': level.description,'options': [{'name': option.optionName, 'value': option.optionPrice } for option in level.priceleveloption_set.all() ]} for level in levels]
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def getShirtSizes(request):
    sizes = ShirtSizes.objects.all()
    data = [{'name': size.name, 'id': size.id} for size in sizes]
    return HttpResponse(json.dumps(data), content_type='application/json')


##################################
# Not Endpoints

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
