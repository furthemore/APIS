# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-10-09 15:54


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0016_priceleveloption_required"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendeeoptions",
            name="optionValue2",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="priceleveloption",
            name="unique",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="priceleveloption",
            name="valueCount",
            field=models.IntegerField(default=1),
        ),
    ]
