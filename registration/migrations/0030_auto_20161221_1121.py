# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-12-21 16:21


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0029_dealer_emailed"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="orderitem",
            name="confirmationCode",
        ),
        migrations.AddField(
            model_name="pricelevel",
            name="group",
            field=models.TextField(blank=True),
        ),
    ]
