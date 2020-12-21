import logging
import os

from django.http import FileResponse, JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


def printNametag(request):
    context = {
        "file": request.GET.get("file", None),
        "next": request.GET.get("next", None),
    }
    return render(request, "registration/printing.html", context)


def servePDF(request):
    filename = request.GET.get("file", None)
    if filename is None:
        return JsonResponse({"success": False, "reason": "Bad request"}, status=400)
    filename = filename.replace("..", "/")
    try:
        fsock = open(f"/tmp/{filename}", "rb")
    except IOError as e:
        return JsonResponse({"success": False, "reason": "file not found"}, status=404)
    response = FileResponse(fsock, content_type="application/pdf")
    # response['Content-Disposition'] = 'attachment; filename=download.pdf'
    response["Access-Control-Allow-Origin"] = "*"
    # os.unlink("/tmp/%s" % filename)
    return response
