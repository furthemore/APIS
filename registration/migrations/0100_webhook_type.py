# Generated by Django 3.2.18 on 2023-03-08 22:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0099_webhook_completed'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentwebhooknotification',
            name='event_type',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='firebase',
            name='token',
            field=models.CharField(help_text="Use 'none' to disable push", max_length=500),
        ),
    ]
