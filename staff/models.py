from django.contrib.auth.models import User
from django.db import models

from registration.models import Event, Person, get_registration_token


class Department(models.Model):
    name = models.CharField(max_length=200, blank=True)
    parent_department = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sub_departments",
        verbose_name="Parent Department",
        help_text="Select a parent department if this is a sub-department",
    )
    volunteerListOk = models.BooleanField(default=False)
    default_landing_page = models.CharField(
        max_length=200,
        blank=True,
        help_text="URL path (e.g., '/staff/portal/') or named URL (e.g., 'staff:portal') for this department's default landing page after login",
    )
    heads = models.ManyToManyField(
        "Staff",
        blank=True,
        related_name="departments_headed",
        verbose_name="Department Heads",
    )
    assistant_heads = models.ManyToManyField(
        "Staff",
        blank=True,
        related_name="departments_assisted",
        verbose_name="Assistant Heads",
    )

    def __str__(self):
        if self.parent_department:
            return f"{self.parent_department.name} > {self.name}"
        return self.name

    def get_all_staff(self):
        """Get all staff in this department and its sub-departments"""

        # Get staff directly in this department
        staff_ids = list(
            Staff.objects.filter(department=self).values_list("id", flat=True)
        )

        # Get staff from all sub-departments recursively
        for sub_dept in self.sub_departments.all():
            staff_ids.extend(sub_dept.get_all_staff().values_list("id", flat=True))

        return Staff.objects.filter(id__in=staff_ids).distinct()


class StaffPosition(models.Model):
    HELD_POSITION = "Held Position"
    STAFF_POOL = "Staff Pool"
    VOLUNTEER_POOL = "Volunteer Pool"

    POSITION_TYPE_CHOICES = [
        (HELD_POSITION, "Held Position"),
        (STAFF_POOL, "Staff Pool"),
        (VOLUNTEER_POOL, "Volunteer Pool"),
    ]

    title = models.CharField(max_length=200)
    position_type = models.CharField(
        max_length=50,
        choices=POSITION_TYPE_CHOICES,
        default=VOLUNTEER_POOL,
    )
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "staff position"
        verbose_name_plural = "staff positions"

    def __str__(self):
        return self.title


class Staff(Person):
    user = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staff_profile",
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staff_members",
    )
    title = models.CharField(max_length=200)
    fandom_name = models.CharField(max_length=200, blank=True)
    registration_token = models.CharField(
        max_length=200,
        default=get_registration_token,
        help_text="Unique token for event registration, rotates after each use"
    )
    onboarding_complete = models.BooleanField(
        default=False,
        help_text="Has this staff member completed their onboarding process?",
    )

    class Meta:
        verbose_name = "Staff Profile"
        verbose_name_plural = "Staff Profiles"
        permissions = [
            ("change_fandom_name", "Can change fandom/credit name"),
        ]
    
    def save(self, *args, **kwargs):
        # Ensure registration_token is set on creation
        if not self.registration_token:
            self.registration_token = get_registration_token()
        super().save(*args, **kwargs)


class StaffEventRegistration(models.Model):
    """Event-specific registration data for staff members"""

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="event_registrations",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="staff_registrations",
    )
    registration_token = models.CharField(
        max_length=200, default=get_registration_token
    )

    # Shirt and swag
    shirt_size = models.ForeignKey(
        "registration.ShirtSizes",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    # Social media
    twitter = models.CharField(max_length=200, blank=True)
    telegram = models.CharField(max_length=200, blank=True)

    # Emergency contact
    contact_name = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=200, blank=True)
    contact_relation = models.CharField(max_length=200, blank=True)

    # Special needs/requests
    special_skills = models.TextField(blank=True)
    special_food = models.TextField(blank=True)
    special_medical = models.TextField(blank=True)

    # Event status
    checked_in = models.BooleanField(default=False)
    registered_date = models.DateTimeField(auto_now_add=True)

    # Notes
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Staff Event Registration"
        verbose_name_plural = "Staff Event Registrations"
        unique_together = [["staff", "event"]]

    def __str__(self):
        return f"{self.staff} - {self.event}"


class StaffPosting(models.Model):
    position = models.ForeignKey(
        StaffPosition,
        on_delete=models.CASCADE,
        related_name="postings",
    )
    event = models.ForeignKey(
        Event,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="staff_postings",
        help_text="Optional: link to a specific event. Leave blank for ongoing positions (e.g., Held Positions)",
    )
    slots = models.IntegerField(
        default=1,
        help_text="Number of open positions for this posting",
    )
    is_open = models.BooleanField(
        default=True,
        verbose_name="Open for Applications",
    )
    application_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional deadline for applications",
    )
    notes = models.TextField(
        blank=True,
        help_text="Event-specific notes or requirements for this posting",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "staff posting"
        verbose_name_plural = "staff postings"
        # Allow same position to be posted multiple times for different events,
        # or as a single ongoing posting with no event
        constraints = [
            models.UniqueConstraint(
                fields=["position", "event"],
                name="unique_position_per_event",
                condition=models.Q(event__isnull=False),
            ),
        ]

    def __str__(self):
        if self.event:
            return f"{self.position.title} - {self.event.name}"
        return f"{self.position.title} (Ongoing)"


class StaffApplicant(Person):
    posting = models.ForeignKey(
        StaffPosting,
        on_delete=models.CASCADE,
        related_name="applicants",
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pending Review"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
            ("withdrawn", "Withdrawn"),
        ],
        default="pending",
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this applicant",
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_applicants",
    )

    class Meta:
        verbose_name = "staff applicant"
        verbose_name_plural = "staff applicants"

    def __str__(self):
        return f"{self.first_name()} {self.last_name()} - {self.posting}"


class StaffInvite(models.Model):
    token = models.CharField(max_length=200, default=get_registration_token)
    email = models.CharField(max_length=200)
    ignore_time_window = models.BooleanField(
        default=False,
        verbose_name="Ignore Registration Time Window",
        help_text="Enabling this option will allow this invite code to disregard the open and close date and time specified in the event. The Valid Until setting on this form will still apply",
    )
    valid_until = models.DateTimeField(verbose_name="Valid Until")
    used = models.BooleanField(default=False)
    used_date = models.DateTimeField(null=True, blank=True, verbose_name="Used Date")
    sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Staff Invite"
        verbose_name_plural = "Staff Invites"

    def __str__(self):
        return f"{self.email} - {self.token}"
