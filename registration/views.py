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
    depts = Department.objects.get(volunteerListOk=True)
    data = json.dumps(depts)
    return HttpResponse(data, content_type='application/json')
