# Handwritten on 2026-01-12 12:30

from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension

class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0109_more_terminal_settings")
    ]

    operations = [
        TrigramExtension()
    ]
