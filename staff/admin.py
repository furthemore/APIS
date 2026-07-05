from django.contrib import admin

from staff.models import Department, Staff, StaffPosition


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "volunteerListOk")
    filter_horizontal = ("heads", "assistant_heads")


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
        "department",
        "user",
        "email",
        "phone",
    )
    list_filter = ("title", "department")
    search_fields = (
        "legal_first_name",
        "legal_last_name",
        "preferred_first_name",
        "preferred_last_name",
        "fandom_name",
        "email",
        "user__username",
        "user__email",
    )
    autocomplete_fields = ["user"]
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
                    "user",
                    "department",
                    "title",
                    "registration_token",
                )
            },
        ),
    )
