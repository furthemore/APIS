from django.http import HttpResponse

from .models import *

# Create your views here.

def index(request):
    return HttpResponse("Registration Index")

