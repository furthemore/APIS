# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-07-22 00:29


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0070_auto_20180719_1728"),
    ]

    operations = [
        migrations.RemoveField(model_name="event", name="dealerBasePriceLevel",),
        migrations.AddField(
            model_name="event",
            name="dealerDiscount",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="dealerEvent",
                to="registration.Discount",
            ),
        ),
    ]
