from django.contrib.auth.models import User
from django.db import models

from registration.models import Event, Person


class Department(models.Model):
    name = models.CharField(max_length=200, blank=True)
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
        return self.name


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

    class Meta:
        verbose_name_plural = "Staff"


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

