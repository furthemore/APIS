from django.http import HttpResponse
from django.shortcuts import render
import json


from .models import *

# Create your views here.

def index(request):
    context = {}
    return render(request, 'registration/registration-form.html', context)


###################################
# Utilities

def getDepartments(request):
    depts = Department.objects.filter(volunteerListOk=True)
    data = [{'name': item.name, 'id': item.id} for item in depts]
    return HttpResponse(json.dumps(data), content_type='application/json')

def getPriceLevels(request):
    levels = PriceLevel.objects.filter(public=True)
    data = [{'name': level.name, 'options': [{'name': option.optionName} for option in level.priceleveloption_set.all() ]} for level in levels]
    return HttpResponse(json.dumps(data), content_type='application/json')
