# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from registration.models import Event

from .models import Job, JobRequest, Volunteer

# from hr.models import Event,Staff,Department
# from ops.models import Note


# Create your views here.

events = Event.objects.filter()


@login_required(login_url="/login/")
def master(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    return render(request, "volunteer/master.html", {"events": events, "event": event})


@login_required(login_url="/login/")
def ControlsV1EventRequests(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    output = {}
    for x in JobRequest.objects.filter(event=event, expired=False):
        output[str(x.pk)] = {
            "summary": x.summary,
            "who": x.who,
            "assigned": 0,
        }
        for y in Job.objects.filter(job_request=x, time_out=None):
            output[str(x.pk)]["assigned"] = output[str(x.pk)]["assigned"] + 1
    return JsonResponse(output)


@login_required(login_url="/login/")
def ControlsV1EventVolunteers(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    volunteers = Volunteer.objects.filter(event=event)
    output = {}
    for x in volunteers:
        output[str(x.pk)] = {
            "pk": "BRCD_" + str(event.pk) + str(x.pk),
            "pki": str(x.pk),
            "first_name": x.attendee.attendee.firstName,
            "last_name": x.attendee.attendee.lastName,
            "fan_name": x.attendee.badgeName,
            "badge_number": x.attendee.badgeNumber,
            "phone_number": x.attendee.phone,
            "contact_handle": x.contactHandle,
            "checked_in": x.checkedIn,
            "on_job": x.onJob(),
            "last_job": x.lastJob(),
            "current_job": x.currentDisplayJob(),
        }
    return JsonResponse(output)


@login_required(login_url="/login/")
def ControlsV1EventVolunteer(request, event_id, volunteer_id):
    event = get_object_or_404(Event, pk=event_id)
    x = get_object_or_404(Volunteer, pk=volunteer_id)
    output[str(x.pk)] = {
        "pk": "BRCD_" + str(event.pk) + str(x.pk),
        "pki": str(x.pk),
        "first_name": x.attendee.attendee.firstName,
        "last_name": x.attendee.attendee.lastName,
        "fan_name": x.attendee.badgeName,
        "badge_number": x.attendee.badgeNumber,
        "phone_number": x.attendee.phone,
        "contact_handle": x.contactHandle,
        "checked_in": x.checkedIn,
        "on_job": x.onJob(),
        "last_job": x.lastJob(),
        "current_job": x.currentDisplayJob(),
    }
    return JsonResponse(output)


def ControlsV1EventVolunteerCheckIn(request, event_id, volunteer_id):
    event = get_object_or_404(Event, pk=event_id)
    x = get_object_or_404(
        Volunteer, pk=str(volunteer_id).replace("BRCD_" + event_id, "")
    )
    output = {"message": " ", "status": "secondary"}
    if x.checked_in == False:
        x.checked_in = True
        x.save()
        output["message"] = "Volunteer has been checked in!"
        output["status"] = "success"
        return JsonResponse(output)
    pass


def ControlsV1EventVolunteerClockIn(request, event_id, volunteer_id):
    event = get_object_or_404(Event, pk=event_id)
    x = get_object_or_404(
        Volunteer, pk=str(volunteer_id).replace("BRCD_" + event_id, "")
    )
    # quick
    nei = Job(
        volunteer=x,
        timeIn=timezone.now(),
        timeOut=None,
        # BOOKMARK: todo - staff relation with django DB
        staffIn=request.user,
    )
    nei.save()
    output = {}
    output["message"] = "Clocked In"
    output["status"] = "success"
    output["job"] = {
        "pk": nei.pk,
    }
    return JsonResponse(output)


def ControlsV1EventVolunteerClockOut(request, event_id, volunteer_id):
    event = get_object_or_404(Event, pk=event_id)
    x = get_object_or_404(
        Volunteer, pk=str(volunteer_id).replace("BRCD_" + event_id, "")
    )
    # quick
    j = x.currentJob()
    j.timeOut = timezone.now()
    j.staffOut = request.user
    j.save()
    output = {}
    output["message"] = "Clocked Out"
    output["status"] = "success"
    output["job"] = {
        "pk": j.pk,
    }
    return JsonResponse(output)


def ControlsV1EventVolunteerClockInLong(request, event_id, volunteer_id):
    event = get_object_or_404(Event, pk=event_id)
    x = get_object_or_404(Volunteer, pk=volunteer_id)
    pass


def ControlsV1EventVolunteerClockOutLong(request, event_id, volunteer_id):
    event = get_object_or_404(Event, pk=event_id)
    x = get_object_or_404(Volunteer, pk=volunteer_id)
    pass


def ControlsV1EventVolunteerTimesheet(request, event_id, volunteer_id):
    event = get_object_or_404(Event, pk=event_id)
    x = get_object_or_404(Volunteer, pk=volunteer_id)
    output = {}
    output[str(x.pk)] = []
    totals = timezone.timedelta(minutes=0)
    for y in Job.objects.filter(volunteer=x).order_by("timeIn"):
        output[str(x.pk)].append(
            (
                timezone.localtime(y.timeIn).strftime("%a %I:%M"),
                str((y.duration().days * 24) + y.duration().seconds // 3600)
                + " Hours, "
                + str((y.duration().seconds // 60) % 60)
                + " Minutes",
                y.detail,
                y.multiplier,
                str(y.staffIn),
                str(y.staffOut),
            )
        )
        totals = totals + y.duration()
        # str((timezone.timedelta(minutes=y.duration()).days * 24)+timezone.timedelta(minutes=y.duration()).seconds//3600)+" Hours, "+str((timezone.timedelta(minutes=y.duration()).seconds//60)%60)+" Minutes"
    output["total"] = (
        str((totals.days * 24) + totals.seconds // 3600)
        + " Hours, "
        + str((totals.seconds // 60) % 60)
        + " Minutes"
    )
    return JsonResponse(output)


def ControlsV1EventRecent(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    pass


def ControlsV1EventRegister(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    rd = json.loads(request.body)
    v = Volunteer()
    v.event = event
    # todo: attendee integration
    v.contact_handle = rd["contact"]
    if rd["mode"] != "Quick":
        # todo: attendee integration
        # v.first_name = rd['first_name']
        # v.last_name = rd['last_name']
        # v.phone_number = rd['phone_number']
        pass
    v.save()
    return JsonResponse({"status": "Registered", "fan_name": v.fan_name})


def ControlsV1EventRequestsDone(request, event_id, request_id):
    event = get_object_or_404(Event, pk=event_id)
    x = get_object_or_404(JobRequest, pk=request_id)
    x.expired = True
    x.save()
    return JsonResponse({"status": "Request marked as done"})
