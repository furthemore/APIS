from django.db import models

from registration.models import Event


class Department(models.Model):
    name = models.CharField(max_length=200, blank=True)
    volunteerListOk = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class StaffPosition(models.Model):
    title = models.CharField(max_length=200)
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL
    )
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    is_open = models.BooleanField(default=True, verbose_name="Open")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "staff position"
        verbose_name_plural = "staff positions"

    def __str__(self):
        return self.title
