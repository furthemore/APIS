# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-13 00:55


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0066_temptoken"),
    ]

    operations = [
        migrations.AlterField(
            model_name="temptoken",
            name="usedDate",
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name="temptoken",
            name="validUntil",
            field=models.DateTimeField(),
        ),
    ]
