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
