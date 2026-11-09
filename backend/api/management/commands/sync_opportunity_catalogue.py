import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from api.models import ServiceCatalogue
from api.services.opportunity_catalogue import OPPORTUNITY_CATALOGUE_NAME


class Command(BaseCommand):
    help = "Import the current Opportunity Assessment catalogue into Service Catalogue."

    def handle(self, *args, **options):
        source = settings.BASE_DIR.parent / "refer doc" / "WPM_Pulse_OA_Task_Scoping.html"
        try:
            text = source.read_text(encoding="utf-8")
            rows = json.JSONDecoder().raw_decode(text.split("const CAT=", 1)[1])[0]
        except (OSError, IndexError, json.JSONDecodeError) as error:
            raise CommandError(f"Unable to read Opportunity Assessment catalogue from {source}: {error}") from error

        if not isinstance(rows, list) or not rows or any(not isinstance(row, list) or len(row) < 9 for row in rows):
            raise CommandError("Opportunity Assessment catalogue has an invalid row format.")

        existing_count = ServiceCatalogue.objects.filter(catalogue=OPPORTUNITY_CATALOGUE_NAME).count()
        if existing_count:
            if existing_count == len(rows):
                self.stdout.write(self.style.SUCCESS(f"Catalogue already contains {existing_count} rows; left unchanged."))
                return
            raise CommandError(
                f"Found {existing_count} existing rows for {OPPORTUNITY_CATALOGUE_NAME}; "
                "refusing to append or overwrite them."
            )

        catalogue_rows = [
            ServiceCatalogue(
                catalogue=OPPORTUNITY_CATALOGUE_NAME,
                product=row[0],
                l1=row[1],
                l2=row[2],
                l3=row[3],
                l4=row[4],
                direction=row[5],
                current_ownership=row[6],
                average_handle_time=row[7],
                task_name=row[8],
            )
            for row in rows
        ]
        with transaction.atomic():
            ServiceCatalogue.objects.bulk_create(catalogue_rows, batch_size=500)

        self.stdout.write(self.style.SUCCESS(f"Imported {len(catalogue_rows)} rows into Service Catalogue."))