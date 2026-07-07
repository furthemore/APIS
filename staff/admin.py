from django.contrib import admin

from staff.models import Department, Staff, StaffApplicant, StaffInvite, StaffPosition, StaffPosting


@admin.action(description="Send staff invitation email")
def send_staff_invite_email(modeladmin, request, queryset):
    from registration import tasks
    from django.contrib import messages
    
    if queryset.count() == 0:
        messages.error(request, "No invites selected")
        return

    for invite in queryset:
        tasks.send_new_staff_email_task.delay(invite.id)
        invite.sent = True
        invite.save()
    
    if queryset.count() > 1:
        messages.success(
            request, f"Successfully sent emails to {queryset.count()} staff members"
        )
    else:
        messages.success(request, f"Successfully sent email to {queryset[0].email}")


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
    list_display = ("name", "parent_department", "volunteerListOk")
    list_filter = ("parent_department",)
    search_fields = ("name",)
    filter_horizontal = ("heads", "assistant_heads")
    fieldsets = (
        (None, {
            "fields": ("name", "parent_department", "volunteerListOk")
        }),
        ("Leadership", {
            "fields": ("heads", "assistant_heads")
        }),
        ("Settings", {
            "fields": ("default_landing_page",)
        }),
    )


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


@admin.register(StaffInvite)
class StaffInviteAdmin(admin.ModelAdmin):
    actions = [send_staff_invite_email]
    list_display = ["email", "token", "valid_until", "sent", "used", "used_date"]
    list_filter = ["sent", "used"]
    readonly_fields = ["token", "used", "used_date"]
    search_fields = ["email", "token"]
    fields = [
        "token",
        "email",
        "valid_until",
        "ignore_time_window",
        "used",
        "used_date",
        "sent",
    ]


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
