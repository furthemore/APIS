from django.http import HttpResponse


def openings(request):
    return HttpResponse("Hello world - staff openings")


def apply(request):
    return HttpResponse("Hello world - staff apply")


def application(request):
    return HttpResponse("Hello world - staff application")


def portal(request):
    return HttpResponse("Hello world - staff portal")
