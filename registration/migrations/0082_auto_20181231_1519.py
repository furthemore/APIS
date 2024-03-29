# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2018-12-31 20:19


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0081_merge_20181231_1518"),
        ("registration", "0080_cart"),
    ]

    operations = [
        migrations.CreateModel(
            name="Charity",
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
                (
                    "url",
                    models.CharField(
                        blank=True,
                        help_text="Charity link",
                        max_length=500,
                        verbose_name="URL",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AlterModelOptions(
            name="order",
            options={"permissions": (("issue_refund", "Can create refunds"),)},
        ),
        migrations.RemoveField(
            model_name="cart",
            name="ipAddress",
        ),
        migrations.AddField(
            model_name="badge",
            name="printCount",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="event",
            name="badgeTheme",
            field=models.CharField(
                default="apis",
                help_text="Name of badge theme to use for printing",
                max_length=200,
                verbose_name="Badge Theme",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="codeOfConduct",
            field=models.CharField(
                blank=True,
                default="/code-of-conduct",
                help_text="Link to code of conduct agreement",
                max_length=500,
                verbose_name="Code of Conduct",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="collectAddress",
            field=models.BooleanField(
                default=True,
                help_text="Disable to skip collecting a mailing address for each attendee.",
                verbose_name="Collect Address",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="collectBillingAddress",
            field=models.BooleanField(
                default=True,
                help_text="Disable to skip collecting a billing address for each order. Note that a billing address and buyer email is required to qualify for Square's Chargeback protection.",
                verbose_name="Collect Billing Address",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="dealerEmail",
            field=models.CharField(
                blank=True,
                default=b"registration@furthemore.org",
                help_text="Email to display on error messages for dealer registration",
                max_length=200,
                verbose_name="Dealer Email",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="registrationEmail",
            field=models.CharField(
                blank=True,
                default=b"registration@furthemore.org",
                help_text="Email to display on error messages for attendee registration",
                max_length=200,
                verbose_name="Registration Email",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="staffEmail",
            field=models.CharField(
                blank=True,
                default=b"registration@furthemore.org",
                help_text="Email to display on error messages for staff registration",
                max_length=200,
                verbose_name="Staff Email",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="apiData",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="attendee",
            name="address1",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="attendee",
            name="city",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="attendee",
            name="country",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="attendee",
            name="postalCode",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="attendee",
            name="state",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="badge",
            name="attendee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="registration.Attendee",
            ),
        ),
        migrations.AlterField(
            model_name="cart",
            name="form",
            field=models.CharField(
                choices=[
                    ("Attendee", "Attendee"),
                    ("Staff", "Staff"),
                    ("Dealer", "Dealer"),
                    ("Dealer Assistant", "Dealer Assistant"),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="cart",
            name="transferedDate",
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name="cashdrawer",
            name="action",
            field=models.CharField(
                choices=[
                    ("Open", "Open"),
                    ("Close", "Close"),
                    ("Transaction", "Transaction"),
                    ("Deposit", "Deposit"),
                ],
                default="Open",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="dealer",
            name="event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="registration.Event",
            ),
        ),
        migrations.AlterField(
            model_name="dealer",
            name="tableSize",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="registration.TableSize",
            ),
        ),
        migrations.AlterField(
            model_name="dealerasst",
            name="attendee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="registration.Attendee",
            ),
        ),
        migrations.AlterField(
            model_name="dealerasst",
            name="event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="registration.Event",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="allowOnlineMinorReg",
            field=models.BooleanField(
                default=False,
                help_text="Allow registration for anyone age 13 and older online. Otherwise, registration is restricted to those 18 or older.",
                verbose_name="Allow online minor registration",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="attendeeRegEnd",
            field=models.DateTimeField(verbose_name="Attendee Registration End"),
        ),
        migrations.AlterField(
            model_name="event",
            name="attendeeRegStart",
            field=models.DateTimeField(verbose_name="Attendee Registration Start"),
        ),
        migrations.AlterField(
            model_name="event",
            name="dealerDiscount",
            field=models.ForeignKey(
                blank=True,
                help_text="Apply a discount for any dealer registrations",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="dealerEvent",
                to="registration.Discount",
                verbose_name="Dealer Discount",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="dealerRegEnd",
            field=models.DateTimeField(verbose_name="Dealer Registration End"),
        ),
        migrations.AlterField(
            model_name="event",
            name="dealerRegStart",
            field=models.DateTimeField(
                help_text="Start date and time for dealer applications",
                verbose_name="Dealer Registration Start",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="default",
            field=models.BooleanField(
                default=False,
                help_text="The first default event will be used as the basis for all current event configuration",
                verbose_name="Default",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="eventEnd",
            field=models.DateField(verbose_name="Event End Date"),
        ),
        migrations.AlterField(
            model_name="event",
            name="eventStart",
            field=models.DateField(verbose_name="Event Start Date"),
        ),
        migrations.AlterField(
            model_name="event",
            name="newStaffDiscount",
            field=models.ForeignKey(
                blank=True,
                help_text="Apply a discount for new staff registrations",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="newStaffEvent",
                to="registration.Discount",
                verbose_name="New Staff Discount",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="onlineRegEnd",
            field=models.DateTimeField(verbose_name="On-site Registration End"),
        ),
        migrations.AlterField(
            model_name="event",
            name="onlineRegStart",
            field=models.DateTimeField(
                help_text="Start time for /registration/onsite form",
                verbose_name="On-site Registration Start",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="staffDiscount",
            field=models.ForeignKey(
                blank=True,
                help_text="Apply a discount for any staff registrations",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="staffEvent",
                to="registration.Discount",
                verbose_name="Staff Discount",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="staffRegEnd",
            field=models.DateTimeField(verbose_name="Staff Registration End"),
        ),
        migrations.AlterField(
            model_name="event",
            name="staffRegStart",
            field=models.DateTimeField(
                help_text="(Not currently enforced)",
                verbose_name="Staff Registration Start",
            ),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="priceLevel",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="registration.PriceLevel",
            ),
        ),
        migrations.AlterField(
            model_name="staff",
            name="attendee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="registration.Attendee",
            ),
        ),
        migrations.AlterField(
            model_name="staff",
            name="event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="registration.Event",
            ),
        ),
        migrations.AlterField(
            model_name="tablesize",
            name="event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="registration.Event",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="charity",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="registration.Charity",
            ),
        ),
    ]
