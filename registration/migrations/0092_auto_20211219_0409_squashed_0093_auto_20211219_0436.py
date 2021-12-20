# Generated by Django 2.2.25 on 2021-12-20 07:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('registration', '0092_auto_20211219_0409'), ('registration', '0093_auto_20211219_0436')]

    dependencies = [
        ('registration', '0091_alter_firebase_webview'),
    ]

    operations = [
        migrations.CreateModel(
            name='Venue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=200)),
                ('address', models.CharField(blank=True, max_length=200)),
                ('website', models.CharField(blank=True, max_length=500)),
                ('city', models.CharField(blank=True, max_length=200)),
                ('country', models.CharField(blank=True, max_length=200)),
                ('postalCode', models.CharField(blank=True, max_length=20)),
                ('state', models.CharField(blank=True, max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='event',
            name='venue',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='registration.Venue'),
        ),
    ]
