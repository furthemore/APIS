import os

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render


def printNametag(request):
    context = {
        "file": request.GET.get("file", None),
        "next": request.GET.get("next", None),
    }
    return render(request, "registration/printing.html", context)


def servePDF(request):
    filename = request.GET.get("file", None)
    if filename is None:
        return JsonResponse({"success": False})
    filename = filename.replace("..", "/")
    try:
        fsock = open("/tmp/%s" % filename)
    except IOError as e:
        return JsonResponse({"success": False})
    response = HttpResponse(fsock, content_type="application/pdf")
    # response['Content-Disposition'] = 'attachment; filename=download.pdf'
    fsock.close()
    os.unlink("/tmp/%s" % filename)
    return response
