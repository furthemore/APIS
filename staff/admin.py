from django.contrib import admin

from staff.models import Department, Staff, StaffApplicant, StaffPosition, StaffPosting


@admin.action(description="Mark onboarding as complete")
def mark_onboarding_complete(modeladmin, request, queryset):
    updated = queryset.update(onboarding_complete=True)
    modeladmin.message_user(
        request,
        f"{updated} staff member(s) marked as onboarding complete.",
    )


@admin.action(description="Mark onboarding as incomplete")
def mark_onboarding_incomplete(modeladmin, request, queryset):
    updated = queryset.update(onboarding_complete=False)
    modeladmin.message_user(
        request,
        f"{updated} staff member(s) marked as onboarding incomplete.",
    )


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
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = (
        "legal_first_name",
        "legal_last_name",
        "fandom_name",
        "title",
        "department",
        "user",
        "onboarding_complete",
        "email",
        "phone",
    )
    list_filter = ("title", "department", "onboarding_complete")
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
    raw_id_fields = ["user"]
    actions = [mark_onboarding_complete, mark_onboarding_incomplete]
    
    def get_fieldsets(self, request, obj=None):
        """Dynamically build fieldsets based on permissions"""
        fieldsets = [
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
                        "onboarding_complete",
                        "registration_token",
                    )
                },
            ),
        ]
        return fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        """Make fandom_name readonly unless user has the special permission"""
        readonly = []
        
        # Check if user has permission to change fandom_name
        if not request.user.has_perm('staff.change_fandom_name'):
            readonly.append('fandom_name')
        
        return readonly


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
