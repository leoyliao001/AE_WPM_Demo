"""One-off backfill of the Country field for BpmRofo/BpmActual.

The bpm_rofo and bpm_actual tables were originally imported from the
"BPM ROFO" and "BPM Actual" sheets of Migration Tracking (1).xlsx in the
same row order as the spreadsheet (row 0 -> id 1, row 1 -> id 2, ...), and
the row counts still match exactly. This script re-reads the Country
column from those sheets and writes it back onto the matching row by id.
"""
import os
import sys
from pathlib import Path

import pandas as pd
import django

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import transaction

from api.models import BpmActual, BpmRofo

EXCEL_PATH = BACKEND_DIR.parent / "Migration Tracking (1).xlsx"


def clean_text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


@transaction.atomic
def backfill(model, sheet_name):
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name, header=0)
    countries = [clean_text(v) for v in df["Country"].tolist()]

    rows = list(model.objects.order_by("id"))
    if len(rows) != len(countries):
        raise RuntimeError(
            f"{sheet_name}: row count mismatch (db={len(rows)} excel={len(countries)}); "
            "refusing to backfill positionally."
        )

    updated = 0
    for row, country in zip(rows, countries):
        if row.country != country:
            row.country = country
            row.save(update_fields=["country"])
            updated += 1
    return updated, len(rows)


if __name__ == "__main__":
    rofo_updated, rofo_total = backfill(BpmRofo, "BPM ROFO")
    print(f"BpmRofo: updated {rofo_updated}/{rofo_total}")
    actual_updated, actual_total = backfill(BpmActual, "BPM Actual")
    print(f"BpmActual: updated {actual_updated}/{actual_total}")
