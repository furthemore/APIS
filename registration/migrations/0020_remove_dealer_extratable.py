# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-10-13 23:37


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0019_auto_20161013_1813"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="dealer",
            name="extraTable",
        ),
    ]
