from django.contrib import admin

from staff.models import Department, Staff, StaffPosition


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "volunteerListOk")


@admin.register(StaffPosition)
class StaffPositionAdmin(admin.ModelAdmin):
    list_display = ("title", "position_type", "department")
    list_filter = ("position_type", "department")


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        "legal_first_name",
        "legal_last_name",
        "fandom_name",
        "title",
        "email",
        "phone",
    )
    list_filter = ("title",)
    search_fields = (
        "legal_first_name",
        "legal_last_name",
        "preferred_first_name",
        "preferred_last_name",
        "fandom_name",
        "email",
    )
    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    ("legal_first_name", "legal_last_name"),
                    ("preferred_first_name", "preferred_last_name"),
                    "fandom_name",
                    "birthdate",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "email",
                    "phone",
                    ("email_ok", "survey_ok"),
                )
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "street_address_1",
                    "street_address_2",
                    ("city", "state"),
                    ("country", "postal_code"),
                )
            },
        ),
        (
            "Staff Information",
            {
                "fields": (
                    "title",
                    "registration_token",
                )
            },
        ),
    )
