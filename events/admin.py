# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Room,Panelist,Panel,PanelRequestType,PanelRequest,PanelComment,PanelSlot,Track
from import_export.admin import ImportExportModelAdmin
# Register your models here.

class RoomAdmin(ImportExportModelAdmin):
	list_filter = ['event']

class PanelistAdmin(ImportExportModelAdmin):
	list_filter = ['event']

class PanelAdmin(ImportExportModelAdmin):
	list_display = ('title','room','panelist','time_start','duration','setup_time','type','r18')
	list_filter = ['event']

class PanelSlotAdmin(ImportExportModelAdmin):
	list_filter = ['event']

admin.site.register(Panel,PanelAdmin)
admin.site.register(Panelist,PanelistAdmin)
admin.site.register(Room,RoomAdmin)
admin.site.register(PanelRequest)
admin.site.register(PanelRequestType)
admin.site.register(PanelComment)
admin.site.register(PanelSlot,PanelSlotAdmin)
admin.site.register(Track)
