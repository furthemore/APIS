# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

# Create your models here.


class Volunteer(models.Model):
    attendee = models.ForeignKey("registration.Badge")
    contactHandle = models.CharField(max_length=50, blank=True, null=True)
    checkedIn = models.BooleanField(default=False)
    dateEntered = models.DateTimeField(auto_now_add=True)
    dateUpdated = models.DateTimeField(auto_now=True)

    def onJob(self):
        if (
            Job.objects.filter(volunteer=self, timeOut=None).order_by("-timeIn").first()
            == None
        ):
            return False
        return True

    def lastJob(self):
        j = Job.objects.filter(volunteer=self).order_by("-timeIn").first()
        if j == None:
            return None
        if j.detail == "":
            j.detail = "No Details"
        return (
            str(timezone.localtime(j.timeIn).strftime("%m/%d/%Y %H:%M"))
            + " - "
            + str(j.detail)
        )

    def currentDisplayJob(self):
        j = Job.objects.filter(volunteer=self, timeOut=None).order_by("-timeIn").first()
        if j == None:
            return None
        if j.detail == "":
            j.detail = "No Details"
        return (
            str(timezone.localtime(j.timeIn).strftime("%m/%d/%Y %H:%M"))
            + " - "
            + str(j.detail)
        )

    def currentJob(self):
        return Job.objects.filter(volunteer=self, timeOut=None).first()

    def __str__(self):
        return self.attendee.badgeName


class JobRequest(models.Model):
    event = models.ForeignKey("registration.Event")
    summary = models.CharField(max_length=250, blank=True, null=True)
    who = models.CharField(max_length=140, blank=True, null=True)
    expired = models.BooleanField(default=False)


class Job(models.Model):
    MULTIPLIERS = (
        (1, "No Multiplier"),
        (1.5, "1.5x Multiplier"),
        (2, "2x Multiplier"),
    )
    volunteer = models.ForeignKey(Volunteer)
    timeIn = models.DateTimeField()
    timeOut = models.DateTimeField(blank=True, null=True)
    detail = models.TextField(blank=True)
    jobRequest = models.ForeignKey(JobRequest, blank=True, null=True)
    staffIn = models.ForeignKey(
        "registration.Staff", blank=True, null=True, related_name="staffIn"
    )
    staffOut = models.ForeignKey(
        "registration.Staff", blank=True, null=True, related_name="staffOut"
    )
    multiplier = models.IntegerField(choices=MULTIPLIERS, default=1)

    def completed(self):
        if self.timeOut == None:
            return False
        return True

    def duration(self):
        try:
            return (self.timeOut - self.timeIn) * self.multiplier
        except:
            return (
                timezone.localtime(timezone.now()) - timezone.localtime(self.timeIn)
            ) * self.multiplier

    def __str__(self):
        return self.volunteer.attendee.badgeName
