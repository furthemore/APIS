# Generated by Django 2.2.25 on 2022-02-07 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0094_add_preferred_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cashdrawer',
            name='action',
            field=models.CharField(choices=[('Open', 'Open'), ('Close', 'Close'), ('Transaction', 'Transaction'), ('Deposit', 'Deposit'), ('Drop', 'Drop'), ('Pickup', 'Pickup')], default='Open', max_length=20),
        ),
    ]