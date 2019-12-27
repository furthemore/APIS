# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-09-17 14:45
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0012_auto_20160830_2154"),
    ]

    operations = [
        migrations.RemoveField(model_name="discount", name="requiredPriceLevel",),
        migrations.AddField(
            model_name="staff",
            name="attendee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="registration.ShirtSizes",
            ),
        ),
        migrations.AddField(
            model_name="staff",
            name="contactName",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="staff",
            name="contactPhone",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="staff",
            name="department",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="registration.Department",
            ),
        ),
        migrations.AddField(
            model_name="staff",
            name="gender",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="staff",
            name="needRoom",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="staff", name="notes", field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="staff",
            name="registrationToken",
            field=models.CharField(default="", max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="staff", name="specialFood", field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="staff",
            name="specialMedical",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="staff",
            name="specialSkills",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="staff",
            name="supervisor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="registration.Staff",
            ),
        ),
        migrations.AddField(
            model_name="staff",
            name="telegram",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="staff",
            name="timesheetAccess",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="staff",
            name="title",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="staff",
            name="twitter",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
