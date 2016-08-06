from django.http import HttpResponse
from django.shortcuts import render
import json


from .models import *

# Create your views here.

def index(request):
    context = {}
    return render(request, 'registration/registration-form.html', context)


###################################
# Payments

def getCart(request):
    #check session for current order
    c = request.session.get('order', Order())
    #return order template
    context = {'cart': c}
    return render(request, 'registration/cart.html', context)

def addToCart(request):
    #create attendee from request post
    #add attendee to session order
    pass

def removeFromCart(request):
    #locate attendee in session order
    #remove attendee from session order
    pass

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
    #todo: date filtering
    levels = PriceLevel.objects.filter(public=True)
    data = [{'name': level.name, 'base_price': level.basePrice.__str__(), 'description': level.description,'options': [{'name': option.optionName} for option in level.priceleveloption_set.all() ]} for level in levels]
    return HttpResponse(json.dumps(data), content_type='application/json')
