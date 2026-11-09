import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from api.models import UserNameList


class Command(BaseCommand):
    help = "Import the user name CSV into an empty user_name_list table."

    def add_arguments(self, parser):
        default_source = Path(settings.BASE_DIR).parent / "refer doc" / "exportGroupMembers_2026-11-9.csv"
        parser.add_argument("--source", default=str(default_source))

    def handle(self, *args, **options):
        source = Path(options["source"])
        if not source.is_file():
            raise CommandError(f"CSV file not found: {source}")
        if UserNameList.objects.exists():
            raise CommandError("user_name_list is not empty; refusing to import duplicate data.")

        records = []
        with source.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if not {"displayName", "mail"}.issubset(reader.fieldnames or []):
                raise CommandError("CSV must contain displayName and mail columns.")
            for line_number, row in enumerate(reader, start=2):
                display_name = (row.get("displayName") or "").strip()
                mail = (row.get("mail") or "").strip()
                if len(display_name) > 255 or len(mail) > 255:
                    raise CommandError(f"Field exceeds 255 characters on CSV line {line_number}.")
                if not display_name and not mail:
                    continue
                records.append(UserNameList(display_name=display_name, mail=mail))

        if not records:
            raise CommandError("CSV contains no importable rows.")

        with transaction.atomic():
            UserNameList.objects.bulk_create(records, batch_size=900)
        self.stdout.write(self.style.SUCCESS(f"Imported {len(records)} user name records."))