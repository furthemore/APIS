import logging
from pathlib import Path
from typing import Union

from django.conf import settings
from django.contrib import messages
from django.core.signing import TimestampSigner
from django.http import FileResponse, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import Context, Template
from gotenberg_client import GotenbergClient
from gotenberg_client.options import (
    MarginType,
    PageMarginsType,
    PageOrientation,
    PageSize,
)

from registration import mqtt
from registration.models import Badge, Dealer, Staff

logger = logging.getLogger(__name__)


def printNametag(request):
    context = {
        "file": request.GET.get("file", None),
        "next": request.GET.get("next", None),
    }
    return render(request, "registration/printing.html", context)


def servePDF(request):
    if getattr(settings, "PRINT_RENDERER", "wkhtmltopdf") == "gotenberg":
        return pdfFromGotenberg(request)
    else:
        return pdfFromDisk(request)


def pdfFromDisk(request: HttpRequest) -> Union[FileResponse, JsonResponse]:
    name = request.GET.get("file", None)
    if not name or not isinstance(name, str):
        return JsonResponse(
            {"success": False, "reason": "Name was missing"}, status=400
        )

    root_dir = getattr(settings, "PDF_DIRECTORY", "/tmp")
    try:
        path = Path(root_dir).joinpath(Path(name).name)
        f = open(path, "rb")
    except IOError:
        return JsonResponse({"success": False, "reason": "IO error"}, status=404)

    response = FileResponse(f, content_type="application/pdf")
    response["Access-Control-Allow-Origin"] = "*"
    return response


def pdfFromGotenberg(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    data = request.GET.get("data", None)
    if not data:
        return JsonResponse({"success": False, "reason": "Missing data"}, status=400)

    signer = TimestampSigner()
    try:
        data_obj = signer.unsign_object(data, max_age=60)
    except:
        return JsonResponse({"success": False, "reason": "Invalid data"}, status=401)

    badge_ids = data_obj.get("badge_ids", [])
    queryset = Badge.objects.filter(id__in=badge_ids)

    badge_groups = {}
    badge_templates = {}

    for badge in queryset:
        level = badge.effectiveLevel()
        if not level or level == Badge.UNPAID:
            messages.warning(
                request, f"skipped printing {badge} because level is {level}"
            )
            continue

        badge_template = badge.event.defaultBadgeTemplate
        if badge_template.id not in badge_templates:
            badge_groups[badge_template.id] = []
            badge_templates[badge_template.id] = (
                badge_template,
                Template(badge_template.template),
            )

        level = str(level)
        if Staff.objects.filter(attendee=badge.attendee, event=badge.event).exists():
            level = "Staff"
        elif Dealer.objects.filter(attendee=badge.attendee, event=badge.event).exists():
            level = "Dealer"

        badge_groups[badge_template.id].append(
            {
                "name": badge.badgeName,
                "level": level,
                "number": badge.badgeNumber,
            }
        )

    with GotenbergClient(settings.GOTENBERG_HOST) as client:
        pdfs = []

        for badge_template_id, badges in badge_groups.items():
            (badge_template, template) = badge_templates[badge_template_id]
            context = Context({"badges": badges})
            rendered = str(template.render(context))

            with client.chromium.html_to_pdf() as route:
                response = (
                    route.size(
                        PageSize(badge_template.paperWidth, badge_template.paperHeight)
                    )
                    .margins(
                        PageMarginsType(
                            MarginType(badge_template.marginTop),
                            MarginType(badge_template.marginBottom),
                            MarginType(badge_template.marginLeft),
                            MarginType(badge_template.marginRight),
                        )
                    )
                    .orient(
                        PageOrientation(
                            PageOrientation.Landscape
                            if badge_template.landscape
                            else PageOrientation.Portrait
                        )
                    )
                    .scale(badge_template.scale)
                    .string_resource(rendered, "index.html")
                    .render_expr("window.badgeReady === true")
                    .run()
                )
                pdfs.append(response.content)

        finalPdf = None

        if len(pdfs) == 0:
            return JsonResponse(
                {"success": False, "reason": "No PDFs were generated"}, status=404
            )
        elif len(pdfs) == 1:
            finalPdf = pdfs[0]
        else:
            with client.merge.merge() as route:
                req = route
                for index, badgePdf in enumerate(pdfs):
                    req._add_in_memory_file(badgePdf, name=f"{index}.pdf")
                response = req.run()
                finalPdf = response.content

        http_resp = HttpResponse()
        http_resp.headers["content-type"] = "application/pdf"
        http_resp.write(finalPdf)

        for badge in queryset:
            badge.printed = True
            badge.save()

        if terminal := data_obj.get("terminal", None):
            topic = f"{mqtt.get_topic('admin', terminal)}/refresh"
            mqtt.send_mqtt_message(topic, None)

        return http_resp
