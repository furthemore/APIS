# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-10-10 22:38


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0017_auto_20161009_1154"),
    ]

    operations = [
        migrations.CreateModel(
            name="Jersey",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("number", models.IntegerField()),
                (
                    "shirtSize",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.ShirtSizes",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(model_name="attendeeoptions", name="optionValue2",),
        migrations.RemoveField(model_name="priceleveloption", name="unique",),
        migrations.RemoveField(model_name="priceleveloption", name="valueCount",),
    ]
