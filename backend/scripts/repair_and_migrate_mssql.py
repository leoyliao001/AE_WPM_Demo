"""Repair known MSSQL migration records, then apply the current API schema."""

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
BASELINE_MIGRATION = "0019_service_catalogue"
MIGRATION_0020 = "0020_project_attributes_access_migration_intake"
MIGRATION_0022 = "0022_migrationintakesubmission_business_case_submission_date"
APPROVAL_MIGRATIONS = [
    "0027_approval_input",
    "0028_project_attributes_access_input_for_approval",
    "0029_delete_approvalinput_and_more",
    "0030_restore_approval_input",
]


def table_exists(table_name):
    return table_name in connection.introspection.table_names()


def column_exists(table_name, column_name):
    with connection.cursor() as cursor:
        return column_name in {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }


def is_applied(migration_name):
    return MigrationRecorder(connection).migration_qs.filter(
        app=APP_LABEL, name=migration_name
    ).exists()


def fake_apply(migration_name):
    print(f"Faking {APP_LABEL}.{migration_name}: schema is already present.")
    call_command("migrate", APP_LABEL, migration_name, fake=True, verbosity=1)


def clear_stale_approval_migration_records():
    if not is_applied("0027_approval_input"):
        return

    if column_exists("project_attributes_access", "input_for_approval"):
        raise RuntimeError(
            "Cannot repair stale approval migration records: "
            "project_attributes_access.input_for_approval still exists."
        )

    print("Removing stale approval migration records with no corresponding table.")
    MigrationRecorder(connection).migration_qs.filter(
        app=APP_LABEL, name__in=APPROVAL_MIGRATIONS
    ).delete()


def main():
    if not is_applied(BASELINE_MIGRATION):
        raise RuntimeError(
            f"Expected {APP_LABEL}.{BASELINE_MIGRATION} to be applied before repair."
        )

    if not is_applied(MIGRATION_0020):
        if not column_exists("project_attributes_access", "migration_intake"):
            raise RuntimeError(
                "Cannot fake 0020: project_attributes_access.migration_intake is absent."
            )
        fake_apply(MIGRATION_0020)

        clear_stale_approval_migration_records()
    call_command("migrate", APP_LABEL, "0021", verbosity=1)

    if not is_applied(MIGRATION_0022):
        if not column_exists(
            "migration_intake_submission", "business_case_submission_date"
        ):
            raise RuntimeError(
                "Cannot fake 0022: migration_intake_submission.business_case_submission_date is absent."
            )
        fake_apply(MIGRATION_0022)

    call_command("migrate", APP_LABEL, verbosity=1)
    call_command("showmigrations", APP_LABEL, verbosity=1)


if __name__ == "__main__":
    main()