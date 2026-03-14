from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0114_remove_attendeeoptions_optionvalue2_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="TempToken",
            new_name="StaffInvite",
        ),
    ]
