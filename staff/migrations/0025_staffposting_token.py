from django.db import migrations, models

import registration.models


class Migration(migrations.Migration):

    dependencies = [
        ("staff", "0024_rename_twitter_to_bluesky"),
    ]

    operations = [
        migrations.AddField(
            model_name="staffposting",
            name="token",
            field=models.CharField(
                default=registration.models.get_registration_token,
                editable=False,
                help_text="Random token used in the public application URL",
                max_length=200,
                unique=True,
            ),
        ),
    ]
