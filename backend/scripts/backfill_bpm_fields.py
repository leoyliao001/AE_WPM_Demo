"""One-off backfill for BpmRofo/BpmActual fields sourced from Migration Tracking (1).xlsx.

The bpm_rofo and bpm_actual tables were originally imported from the
"BPM ROFO" and "BPM Actual" sheets in the same row order as the
spreadsheet (row 0 -> id 1, row 1 -> id 2, ...), and the row counts still
match exactly. This script re-reads columns from those sheets that are not
yet populated in the database and writes them back onto the matching row
by id.
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

# Maps excel column name -> model field name.
COLUMN_FIELD_MAP = {
    "Status": "status",
    "Country": "country",
    "GSC Site to be offshored": "gsc_site",
    "Function": "function",
    "Function ID + Description": "function_id_description",
    "Cost Center": "cost_center",
    "PID": "pid",
    "Part/Not part of ROFO": "part_not_part_of_rofo",
    "GSC Leaders": "gsc_leader",
    "GSC-1 Leaders": "gsc1_leader",
    "BU": "bu",
    "Frontline \nStaff Cost per FTE": "frontline_staff_cost_per_fte",
    "GSC Staff Cost per FTE": "gsc_staff_cost_per_fte",
    "Project Cost": "project_cost",
    "X": "x_column",
    "Base PIDs": "base_pids",
    "Positions to be released in Frontline": "positions_to_be_released_in_frontline",
}


def clean_text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


@transaction.atomic
def backfill(model, sheet_name):
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name, header=0)

    rows = list(model.objects.order_by("id"))
    if len(rows) != len(df):
        raise RuntimeError(
            f"{sheet_name}: row count mismatch (db={len(rows)} excel={len(df)}); "
            "refusing to backfill positionally."
        )

    columns = {col: field for col, field in COLUMN_FIELD_MAP.items() if col in df.columns}
    updated = 0
    for row, (_, excel_row) in zip(rows, df.iterrows()):
        changed_fields = []
        for col, field in columns.items():
            value = clean_text(excel_row[col])
            if getattr(row, field) != value:
                setattr(row, field, value)
                changed_fields.append(field)
        if changed_fields:
            row.save(update_fields=changed_fields)
            updated += 1
    return updated, len(rows)


if __name__ == "__main__":
    rofo_updated, rofo_total = backfill(BpmRofo, "BPM ROFO")
    print(f"BpmRofo: updated {rofo_updated}/{rofo_total}")
    actual_updated, actual_total = backfill(BpmActual, "BPM Actual")
    print(f"BpmActual: updated {actual_updated}/{actual_total}")
