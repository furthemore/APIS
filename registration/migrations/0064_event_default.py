# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-04-25 22:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0063_auto_20180419_0210'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='default',
            field=models.BooleanField(default=False),
        ),
    ]