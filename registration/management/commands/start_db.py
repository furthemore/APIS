from pathlib import Path
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from registration.utils.database import DatabaseStatus, Postgres


class Command(BaseCommand):
    help = "Starts the development postgresql database."

    def add_arguments(self, parser):
        base_dir = Path(settings.BASE_DIR)
        db_dir = (base_dir / "pgdb").absolute()

        parser.add_argument(
            "--db-path",
            type=str,
            default=str(db_dir),
            help=f"Path where the postgresql database will be stopped, default {db_dir}.",
        )

    def handle(self, *args, **options):
        postgres = Postgres(options["db_path"])

        status = postgres.get_status()
        if status == DatabaseStatus.STOPPED:
            postgres.start()

            print("Postgres server started")
        elif status == DatabaseStatus.RUNNING:
            print("Postgres server is already running")
        else:
            print(f"Cannot start Postgres server, invalid status: {status}", file=sys.stderr)
