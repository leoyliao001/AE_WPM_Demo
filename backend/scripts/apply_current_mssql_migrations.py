"""Repair the stale 0027 record and apply the current API migrations forward."""

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_DB_ENGINE", "mssql")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.core.management import call_command
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


APP_LABEL = "api"
STALE_MIGRATION = "0027_approval_input"


def table_exists(table_name):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM sys.tables WHERE name = %s", [table_name])
        return cursor.fetchone() is not None


def column_exists(table_name, column_name):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            [table_name, column_name],
        )
        return cursor.fetchone() is not None


def main():
    recorder = MigrationRecorder(connection)
    stale_record_exists = recorder.migration_qs.filter(
        app=APP_LABEL, name=STALE_MIGRATION
    ).exists()

    if stale_record_exists and not table_exists("approval_input"):
        if column_exists("project_attributes_access", "input_for_approval"):
            raise RuntimeError(
                "Refusing to remove the stale 0027 record because the later "
                "input_for_approval column exists."
            )
        recorder.migration_qs.filter(app=APP_LABEL, name=STALE_MIGRATION).delete()
        print("Removed stale api.0027_approval_input migration record.", flush=True)

    call_command("migrate", APP_LABEL, verbosity=1)

    required_tables = {"working_hours", "approval_workflow", "approval_input"}
    missing_tables = sorted(
        table_name for table_name in required_tables if not table_exists(table_name)
    )
    if missing_tables:
        raise RuntimeError(f"Missing expected MSSQL tables: {', '.join(missing_tables)}")
    if not column_exists("project_attributes_access", "input_for_approval"):
        raise RuntimeError("Missing project_attributes_access.input_for_approval")

    if not recorder.migration_qs.filter(app=APP_LABEL, name="0030_restore_approval_input").exists():
        raise RuntimeError("api.0030_restore_approval_input is not recorded as applied.")

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM approval_input")
        approval_input_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM working_hours")
        working_hours_count = cursor.fetchone()[0]
    print(
        "MSSQL migration complete: "
        f"approval_input_rows={approval_input_count}, "
        f"working_hours_rows={working_hours_count}",
        flush=True,
    )


if __name__ == "__main__":
    main()