from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0113_remove_badge_printcount_printhistory"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="TempToken",
            new_name="StaffInvite",
        ),
    ]
