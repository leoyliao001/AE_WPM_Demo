"""Print the MSSQL migration records and schema needed for repair decisions."""

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

from django.db import connection


def main():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name, applied FROM django_migrations "
            "WHERE app = 'api' ORDER BY applied, name"
        )
        print("=== api migration records ===", flush=True)
        for name, applied in cursor.fetchall():
            print(f"{name} {applied}", flush=True)

        cursor.execute("SELECT name FROM sys.tables ORDER BY name")
        print("=== relevant tables ===", flush=True)
        tables = {row[0] for row in cursor.fetchall()}
        for table_name in (
            "project_attributes_access",
            "migration_intake_submission",
            "working_hours",
            "approval_workflow",
            "approval_input",
        ):
            print(f"{table_name}={table_name in tables}", flush=True)

        print("=== relevant columns ===", flush=True)
        for table_name in (
            "project_attributes_access",
            "migration_intake_submission",
        ):
            cursor.execute(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = %s "
                "ORDER BY ORDINAL_POSITION",
                [table_name],
            )
            columns = [row[0] for row in cursor.fetchall()]
            print(f"{table_name}={','.join(columns)}", flush=True)


if __name__ == "__main__":
    main()