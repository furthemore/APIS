# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-02-17 09:00


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0086_rename_tables"),
    ]

    operations = [
        migrations.RenameField(
            model_name="event",
            old_name="onlineRegEnd",
            new_name="onsiteRegEnd",
        ),
        migrations.RenameField(
            model_name="event",
            old_name="onlineRegStart",
            new_name="onsiteRegStart",
        ),
    ]
