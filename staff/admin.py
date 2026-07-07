from django.contrib import admin

from staff.models import Department, Staff, StaffApplicant, StaffPosition, StaffPosting


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "volunteerListOk")
    filter_horizontal = ("heads", "assistant_heads")


@admin.register(StaffPosition)
class StaffPositionAdmin(admin.ModelAdmin):
    list_display = ("title", "position_type", "department")
    list_filter = ("position_type", "department")
    search_fields = ("title", "description")


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


@admin.register(StaffPosting)
class StaffPostingAdmin(admin.ModelAdmin):
    list_display = ("position", "event", "slots", "is_open", "application_deadline")
    list_filter = ("is_open", "event", "position__department")
    search_fields = ("position__title", "event__name", "notes")
    autocomplete_fields = ["position"]
    # Don't use autocomplete for event since Event admin might not have search_fields
    # Instead use a regular dropdown


@admin.register(StaffApplicant)
class StaffApplicantAdmin(admin.ModelAdmin):
    list_display = (
        "legal_first_name",
        "legal_last_name",
        "posting",
        "status",
        "applied_at",
    )
    list_filter = ("status", "posting__event", "posting__position__department")
    search_fields = (
        "legal_first_name",
        "legal_last_name",
        "preferred_first_name",
        "preferred_last_name",
        "email",
        "posting__position__title",
    )
    autocomplete_fields = ["posting", "reviewed_by"]
    readonly_fields = ("applied_at",)
    fieldsets = (
        (
            "Application",
            {
                "fields": (
                    "posting",
                    "status",
                    ("applied_at", "reviewed_at"),
                    "reviewed_by",
                    "notes",
                )
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    ("legal_first_name", "legal_last_name"),
                    ("preferred_first_name", "preferred_last_name"),
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
            "Registration",
            {
                "fields": ("registration_token",)
            },
        ),
    )
