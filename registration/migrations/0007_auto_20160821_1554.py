# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-08-21 15:54


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0006_auto_20160806_1733"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderitem",
            name="order",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="registration.Order",
            ),
        ),
    ]
