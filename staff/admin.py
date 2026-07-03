from django.contrib import admin

from staff.models import Department, StaffPosition


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "volunteerListOk")


@admin.register(StaffPosition)
class StaffPositionAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "event", "is_open")
    list_filter = ("is_open", "department", "event")
