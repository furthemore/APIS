# Generated by Django 3.2.16 on 2023-01-25 01:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0097_temptoken_ignore_time_window'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='attendeeRegEnd',
            field=models.DateTimeField(verbose_name='Online Attendee Registration End'),
        ),
        migrations.AlterField(
            model_name='event',
            name='attendeeRegStart',
            field=models.DateTimeField(verbose_name='Online Attendee Registration Start'),
        ),
        migrations.AlterField(
            model_name='event',
            name='dealerRegStart',
            field=models.DateTimeField(verbose_name='Dealer Registration Start'),
        ),
        migrations.AlterField(
            model_name='event',
            name='onsiteRegEnd',
            field=models.DateTimeField(verbose_name='On-Site Registration End'),
        ),
        migrations.AlterField(
            model_name='event',
            name='onsiteRegStart',
            field=models.DateTimeField(help_text='Start time for /registration/onsite form', verbose_name='On-Site Registration Start'),
        ),
        migrations.AlterField(
            model_name='event',
            name='staffRegStart',
            field=models.DateTimeField(verbose_name='Staff Registration Start'),
        ),
    ]
