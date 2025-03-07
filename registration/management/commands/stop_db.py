from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from registration.utils.database import DatabaseStatus, Postgres


class Command(BaseCommand):
    help = "Stops the development postgresql database."

    def add_arguments(self, parser):
        base_dir = Path(settings.BASE_DIR)
        db_dir = (base_dir / "pgdb").absolute()

        parser.add_argument(
            "--db-path",
            type=str,
            default=str(db_dir),
            help=f"Path where the postgresql database will be stopped, default {db_dir}.",
        )
        parser.add_argument(
            "--delete",
            type=bool,
            default=False,
            help="Whether or not to delete the database after it has been stopped, default False."
        )

    def handle(self, *args, **options):
        postgres = Postgres(options["db_path"])

        status = postgres.get_status()
        if status == DatabaseStatus.RUNNING:
            postgres.stop()

        if options["delete"]:
            postgres.delete()
