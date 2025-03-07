from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from registration.utils.database import DatabaseStatus, Postgres


config_block = """
DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '{db_path}',
        'NAME' : '{db_name}',
    }}
}}
"""

config_block_with_test = """
DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '{db_path}',
        'NAME' : '{db_name}',
        'TEST' : {{
            'NAME' : '{test_db_name}',
        }}
    }}
}}
"""


class Command(BaseCommand):
    help = "Creates a development postgresql database."

    def add_arguments(self, parser):
        base_dir = Path(settings.BASE_DIR)
        db_dir = (base_dir / "pgdb").absolute()

        parser.add_argument(
            "--db-path",
            type=str,
            default=str(db_dir),
            help=f"Path where the postgresql database will be created, default {db_dir}.",
        )
        parser.add_argument(
            "--db-name",
            type=str,
            default="apis_dev",
            help="The database name to create, default apis_dev.",
        )
        parser.add_argument(
            "--test-db-name",
            type=str,
            default="apis_test",
            help="The test database name to create, default apis_test.",
        )
        parser.add_argument(
            "--skip-test-db",
            type=bool,
            default=False,
            help="Whether or not to skip creating the test database, default False.",
        )
        parser.add_argument(
            "--silent",
            type=bool,
            default=False,
            help="Whether to suppress configuration information, default False."
        )

    def handle(self, *args, **options):
        postgres = Postgres(options["db_path"])

        status = postgres.get_status()

        if status in (DatabaseStatus.UNKNOWN, DatabaseStatus.INVALID_DIRECTORY):
            postgres.delete()

            status = DatabaseStatus.DOES_NOT_EXIST

        if status in (DatabaseStatus.DOES_NOT_EXIST, DatabaseStatus.DIRECTORY_EMPTY):
            postgres.init()

            status = DatabaseStatus.STOPPED

        db_name = options["db_name"]
        postgres.create_db(db_name)

        skip_test_db = options["skip_test_db"]
        test_db_name = options["test_db_name"]
        if test_db_name and not skip_test_db:
            postgres.create_db(test_db_name)

        if options["silent"]:
            return

        if test_db_name and not skip_test_db:
            config_text = config_block_with_test.format(
                db_path=postgres.db_path,
                db_name=db_name,
                test_db_name=test_db_name,
            )
        else:
            config_text = config_block.format(
                db_path=postgres.db_path,
                db_name=db_name,
            )

        print(f"Created database {db_name} at {postgres.db_path}")
        print("Add the following to your settings.py")
        print(config_text)
