# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Job, JobRequest, Volunteer

# Register your models here.


class VolunteerAdmin(ImportExportModelAdmin):
    list_display = ("attendee", "checkedIn", "onJob")
    list_filter = ["checkedIn"]
    model = Volunteer


class JobAdmin(ImportExportModelAdmin):
    list_display = (
        "volunteer",
        "timeIn",
        "timeOut",
        "detail",
        "staffIn",
        "staffOut",
        "multiplier",
    )


admin.site.register(Volunteer, VolunteerAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(JobRequest)
