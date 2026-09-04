import os
from datetime import datetime

import pandas as pd
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import transaction
from api.models import MigrationIntakeSubmission, OpportunityAssessment

EXCEL_PATH = r"C:\fcous\AE WPM Demo\Migration Tracking (1).xlsx"
SHEET_NAME = "Project Tracker"


def clean_text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def clean_list(value):
    text = clean_text(value)
    return [text] if text else []


def as_iso_date(value):
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    try:
        return pd.to_datetime(value).date().isoformat()
    except Exception:
        return ""


def status_from_row(row):
    actual_stage = clean_text(row.get("Actual Stage", "")).lower()
    overall = clean_text(row.get("OverAll Progress", "")).lower()
    planned_stage = clean_text(row.get("Planned Stage", "")).lower()

    if actual_stage in {"complete", "go live"} or "complete" in planned_stage or "complete" in actual_stage:
        return "completed"
    if "delay" in overall or "at risk" in overall or "risk" in overall:
        return "at_risk"
    if actual_stage and actual_stage not in {"na", "n/a", "-", "nan"}:
        return "in_progress"
    if planned_stage and planned_stage not in {"na", "n/a", "-", "nan"}:
        return "planning"
    return "new"


@transaction.atomic
def import_project_tracker():
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, header=6)
    imported = 0
    updated = 0

    for _, row in df.iterrows():
        migration_request_id = clean_text(row.get("WPM Unique Identifier"))
        if not migration_request_id:
            continue

        project_name = clean_text(row.get("Project_Name"))
        mm_name = clean_text(row.get("MM Name")).replace(" ", " ").strip()
        migration_type = clean_text(row.get("Migration Type"))
        region = clean_text(row.get("Region"))
        area = clean_text(row.get("Area"))
        country = clean_text(row.get("Country"))
        gsc_site = clean_text(row.get("GSC Site"))
        function_name = clean_text(row.get("Function ID + Description")) or clean_text(row.get("Function"))
        product_name = clean_text(row.get("Product ID + Description"))
        pmo_remarks = clean_text(row.get("PMO Remarks")) or project_name
        fte_value = row.get("Migratable\nFTE")
        fte_number = str(int(float(fte_value))) if pd.notna(fte_value) and str(fte_value).strip() not in {"", "nan"} else "0"

        business_case_date = as_iso_date(row.get("Business Case \nApproved Actual Date "))
        requested_date = as_iso_date(
            row.get("Functional Assessment\nStart Date\nStage 1 \n(6 Weeks)")
            or row.get("Opportunity Assessment\nStart Date \nStage 2 \n(6 Weeks)")
        )

        payload = {
            "migrationRequestId": migration_request_id,
            "requestedDate": requested_date,
            "requestor": mm_name,
            "status": status_from_row(row),
            "projectName": project_name,
            "migrationType": migration_type,
            "migrationTypeValue": migration_type or "",
            "region": region,
            "areas": clean_list(area),
            "countries": clean_list(country),
            "areaCountryPairs": [{"area": area, "country": country}] if area and country else [],
            "defaultLocationStrategies": clean_list(gsc_site),
            "customLocationStrategies": [],
            "locationStrategyCustom": False,
            "customLocationStrategyJustification": "",
            "function": function_name,
            "products": clean_list(product_name),
            "proposedScope": pmo_remarks,
            "languageDependencies": [],
            "fteNumber": fte_number,
            "jl2": "0",
            "jl3": "0",
            "jl4": "0",
            "jobLevelTotal": 0,
            "risks": clean_text(row.get("Remarks/ Delay")) or clean_text(row.get("OverAll Progress")),
        }

        obj, created = MigrationIntakeSubmission.objects.update_or_create(
            migration_request_id=migration_request_id,
            defaults={
                "requested_date": payload["requestedDate"],
                "requestor": payload["requestor"],
                "status": payload["status"],
                "project_name": payload["projectName"],
                "migration_type": payload["migrationType"],
                "migration_type_value": payload["migrationTypeValue"],
                "region": payload["region"],
                "areas": payload["areas"],
                "countries": payload["countries"],
                "area_country_pairs": payload["areaCountryPairs"],
                "default_location_strategies": payload["defaultLocationStrategies"],
                "custom_location_strategies": payload["customLocationStrategies"],
                "location_strategy_custom": payload["locationStrategyCustom"],
                "custom_location_strategy_justification": payload["customLocationStrategyJustification"],
                "function_name": payload["function"],
                "products": payload["products"],
                "proposed_scope": payload["proposedScope"],
                "language_dependencies": payload["languageDependencies"],
                "fte_number": payload["fteNumber"],
                "jl2": payload["jl2"],
                "jl3": payload["jl3"],
                "jl4": payload["jl4"],
                "job_level_total": payload["jobLevelTotal"],
                "risks": payload["risks"],
            },
        )

        # MM Name in the tracker is the Migration Manager and should map to
        # OpportunityAssessment.owner, which is the canonical field used for
        # manager-level filtering and linking by migration_request_id.
        if mm_name:
            obj.requestor = mm_name
            obj.save(update_fields=["requestor", "updated_at"])
        if business_case_date:
            try:
                obj.business_case_submission_date = pd.to_datetime(business_case_date)
                obj.save(update_fields=["business_case_submission_date", "updated_at"])
            except Exception:
                pass

        if created:
            imported += 1
        else:
            updated += 1

        OpportunityAssessment.objects.update_or_create(
            migration_request_id=migration_request_id,
            defaults={
                "product": product_name,
                "owner": mm_name,
                "location": gsc_site,
                "l1": function_name,
                "l2": function_name,
                "l3": area or region,
                "l4": project_name,
                "task_name": project_name,
                "task_description": pmo_remarks,
                "gsc_site": gsc_site,
            },
        )

    return imported, updated


if __name__ == "__main__":
    imported, updated = import_project_tracker()
    print(f"Imported={imported} Updated={updated}")
    print(f"MigrationIntakeSubmission count={MigrationIntakeSubmission.objects.count()}")
    print(f"OpportunityAssessment count={OpportunityAssessment.objects.count()}")
