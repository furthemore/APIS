from django.db import models

from registration.models import Event, Person


class Department(models.Model):
    name = models.CharField(max_length=200, blank=True)
    volunteerListOk = models.BooleanField(default=False)

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
    title = models.CharField(max_length=200)
    fandom_name = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = "Staff"
