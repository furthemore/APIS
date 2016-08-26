from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import datetime
import json
import random
import string

from .models import *

# Create your views here.

def index(request):
    context = {}
    return render(request, 'registration/registration-form.html', context)


###################################
# Payments

def getTotal(orderItems):
    total = 0
    if not orderItems: return total
    for item in orderItems:
        itemTotal = item.priceLevel.basePrice
        for option in item.attendeeoptions_set.all():
            itemTotal += option.option.optionPrice
        if item.discount:
            if item.discount.amountOff:
                itemTotal -= item.discount.amountOff
            elif item.discount.percentOff:
                itemTotal -= itemTotal * (item.discount.percentOff/100)
        if itemTotal > 0:
            total += itemTotal
    return total

def getCart(request):
    sessionItems = request.session.get('order_items', [])
    orderItems = list(OrderItem.objects.filter(id__in=sessionItems))
    total = getTotal(orderItems)
    context = {'orderItems': orderItems, 'total': total}
    return render(request, 'registration/cart.html', context)

def addToCart(request):
    #create attendee from request post
    postData = json.loads(request.body)
    pda = postData['attendee']
    pdp = postData['priceLevel']
    pdd = postData['discount'].strip()    

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

    if pdd:
        discount = Discount.objects.get(codeName=pdd)
        if discount.isValid(priceLevel):
            orderItem.discount = discount
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
    order = request.session.get('order', [])
    id = request.post['id']
    #remove attendee from session order
    for item in order:
        if item.id == id: 
            del cart[item]
    request.session.set('order', cart)
    return HttpResponse("Success")    

def cancelOrder(request):
    #remove order from session
    try:
        del request.session['order']
    except KeyError:
        pass
    return HttpResponse("Order Cancelled")

def checkout(request):
    pass



###################################
# Utilities

def getDepartments(request):
    depts = Department.objects.filter(volunteerListOk=True)
    data = [{'name': item.name, 'id': item.id} for item in depts]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getPriceLevels(request):
    now = timezone.now()
    levels = PriceLevel.objects.filter(public=True, startDate__lte=now, endDate__gte=now)
    data = [{'name': level.name, 'base_price': level.basePrice.__str__(), 'description': level.description,'options': [{'name': option.optionName} for option in level.priceleveloption_set.all() ]} for level in levels]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getShirtSizes(request):
    sizes = ShirtSizes.objects.all()
    data = [{'name': size.name, 'id': size.id} for size in sizes]
    return HttpResponse(json.dumps(data), content_type='application/json')


##################################
# Not Endpoints

def getConfirmationCode():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase+string.digits) for _ in range(6))
        
