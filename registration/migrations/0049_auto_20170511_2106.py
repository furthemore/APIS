# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-05-12 01:06


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0048_auto_20170511_2022"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pricelevel",
            name="priceLevelOptions",
        ),
        migrations.AddField(
            model_name="pricelevel",
            name="priceLevelOptions",
            field=models.ManyToManyField(to="registration.PriceLevelOption"),
        ),
    ]
