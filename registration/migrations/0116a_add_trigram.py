# Handwritten on 2026-01-12 12:30

from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("registration", "0116_alter_staffinvite_options_and_more")]

    operations = [TrigramExtension()]
