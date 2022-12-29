# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-07-23 17:06


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Attendee",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("firstName", models.CharField(max_length=200)),
                ("lastName", models.CharField(max_length=200)),
                ("address1", models.CharField(max_length=200)),
                ("address2", models.CharField(blank=True, max_length=200)),
                ("city", models.CharField(max_length=200)),
                ("state", models.CharField(max_length=200)),
                ("country", models.CharField(max_length=200)),
                ("postalCode", models.CharField(max_length=20)),
                ("phone", models.CharField(max_length=20)),
                ("email", models.CharField(max_length=200)),
                ("birthdate", models.DateField()),
                ("badgeName", models.CharField(blank=True, max_length=200)),
                ("badgeNumber", models.IntegerField(null=True)),
                ("badgePrinted", models.BooleanField(default=False)),
                ("emailsOk", models.BooleanField(default=False)),
                ("volunteerContact", models.BooleanField(default=False)),
                ("volunteerDepts", models.CharField(max_length=1000)),
                ("notes", models.TextField()),
                ("parentFirstName", models.CharField(blank=True, max_length=200)),
                ("parentLastName", models.CharField(blank=True, max_length=200)),
                ("parentPhone", models.CharField(blank=True, max_length=20)),
                ("parentEmail", models.CharField(blank=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name="AttendeeOptions",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("optionExtraValue", models.CharField(max_length=200)),
                (
                    "attendee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.Attendee",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Dealer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Department",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Discount",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("codeName", models.CharField(max_length=100)),
                ("percentOff", models.IntegerField(null=True)),
                (
                    "amountOff",
                    models.DecimalField(decimal_places=2, max_digits=6, null=True),
                ),
                ("startDate", models.DateTimeField()),
                ("endDate", models.DateTimeField()),
                ("notes", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="HoldType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "balance",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=6),
                ),
                ("authorizationCode", models.CharField(max_length=100)),
                ("transactionId", models.CharField(max_length=100)),
                ("createdDate", models.DateTimeField(auto_now_add=True)),
                ("settledDate", models.DateTimeField(null=True)),
                ("notes", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("confirmationCode", models.CharField(max_length=100)),
                ("enteredBy", models.CharField(max_length=100)),
                (
                    "attendee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.Attendee",
                    ),
                ),
                (
                    "discount",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.Discount",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.Order",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PriceLevel",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("basePrice", models.DecimalField(decimal_places=2, max_digits=6)),
                ("startDate", models.DateTimeField()),
                ("endDate", models.DateTimeField()),
                ("public", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="PriceLevelOption",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("optionName", models.CharField(max_length=200)),
                ("optionPrice", models.DecimalField(decimal_places=2, max_digits=6)),
                ("OptionExtraType", models.CharField(max_length=100)),
                (
                    "priceLevel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.PriceLevel",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ShirtSizes",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Staff",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="orderitem",
            name="priceLevel",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="registration.PriceLevel",
            ),
        ),
        migrations.AddField(
            model_name="discount",
            name="requiredPriceLevel",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="registration.PriceLevel",
            ),
        ),
        migrations.AddField(
            model_name="attendeeoptions",
            name="option",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="registration.PriceLevelOption",
            ),
        ),
        migrations.AddField(
            model_name="attendeeoptions",
            name="order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="registration.Order"
            ),
        ),
        migrations.AddField(
            model_name="attendee",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="registration.Event"
            ),
        ),
        migrations.AddField(
            model_name="attendee",
            name="holdType",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="registration.HoldType",
            ),
        ),
        migrations.AddField(
            model_name="attendee",
            name="parent",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="registration.Attendee",
            ),
        ),
    ]
