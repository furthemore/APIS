# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-15 15:24


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0055_auto_20171009_1134"),
    ]

    operations = [
        migrations.AddField(
            model_name="dealer",
            name="asstBreakfast",
            field=models.BooleanField(default=False),
        ),
    ]
