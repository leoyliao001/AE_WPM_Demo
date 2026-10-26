"""Copy one local SQLite stakeholder registration into MSSQL without overwriting."""

import json
import os
import sqlite3
import sys
from datetime import timezone as datetime_timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BACKEND_DIR / "db.sqlite3"
PROJECT_ID = int(os.environ.get("STAKEHOLDER_SYNC_PROJECT_ID", "543"))

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ["DJANGO_DB_ENGINE"] = "mssql"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils import timezone as django_timezone

from api.models import MigrationIntakeSubmission, StakeholderRegistration


def decode_json(value, fallback):
    return json.loads(value) if value else fallback


def parse_utc_datetime(value):
    parsed = parse_datetime(value) if value else None
    if parsed is None:
        return None
    if django_timezone.is_naive(parsed):
        return parsed.replace(tzinfo=datetime_timezone.utc)
    return parsed.astimezone(datetime_timezone.utc)


def main():
    with sqlite3.connect(SOURCE_DB) as source:
        project = source.execute(
            "SELECT migration_request_id FROM migration_intake_submission WHERE id = ?",
            [PROJECT_ID],
        ).fetchone()
        if not project:
            raise RuntimeError(f"SQLite project {PROJECT_ID} was not found.")
        migration_request_id = project[0]

        source_row = source.execute(
            "SELECT team_members, assignments, audit_log, revision, updated_by, created_at, updated_at "
            "FROM stakeholder_registration WHERE project_id = ?",
            [PROJECT_ID],
        ).fetchone()
        if not source_row:
            raise RuntimeError(f"SQLite Stakeholder Registration for project {PROJECT_ID} was not found.")

    target_project = MigrationIntakeSubmission.objects.filter(
        migration_request_id=migration_request_id
    ).first()
    if not target_project:
        raise RuntimeError(
            f"MSSQL project '{migration_request_id}' was not found; refusing to create an orphan registration."
        )

    values = {
        "team_members": decode_json(source_row[0], []),
        "assignments": decode_json(source_row[1], {}),
        "audit_log": decode_json(source_row[2], []),
        "revision": source_row[3],
        "updated_by": source_row[4],
    }
    created_at = parse_utc_datetime(source_row[5])
    updated_at = parse_utc_datetime(source_row[6])
    existing = StakeholderRegistration.objects.filter(project=target_project).first()
    if existing:
        if all(getattr(existing, key) == value for key, value in values.items()):
            timestamp_updates = {}
            if created_at and existing.created_at != created_at:
                timestamp_updates["created_at"] = created_at
            if updated_at and existing.updated_at != updated_at:
                timestamp_updates["updated_at"] = updated_at
            if timestamp_updates:
                StakeholderRegistration.objects.filter(pk=existing.pk).update(**timestamp_updates)
            print(
                f"Already synchronized: {migration_request_id}, "
                f"team_members={len(values['team_members'])}, revision={values['revision']}, "
                f"timestamps_corrected={bool(timestamp_updates)}",
                flush=True,
            )
            return
        raise RuntimeError(
            f"MSSQL already has a Stakeholder Registration for '{migration_request_id}' with different data; refusing to overwrite."
        )

    with transaction.atomic():
        registration = StakeholderRegistration.objects.create(project=target_project, **values)
        timestamp_updates = {}
        if created_at:
            timestamp_updates["created_at"] = created_at
        if updated_at:
            timestamp_updates["updated_at"] = updated_at
        if timestamp_updates:
            StakeholderRegistration.objects.filter(pk=registration.pk).update(**timestamp_updates)

    print(
        f"Synchronized {migration_request_id}: project_id={target_project.id}, "
        f"team_members={len(values['team_members'])}, revision={values['revision']}, "
        f"audit_entries={len(values['audit_log'])}.",
        flush=True,
    )


if __name__ == "__main__":
    main()