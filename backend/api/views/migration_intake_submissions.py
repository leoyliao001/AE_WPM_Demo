"""
Migration Intake submissions — Handsontable grid over migration_intake_submission.
"""

from __future__ import annotations

import json

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationIntakeSubmission
from api.permissions.attributes_access import require_attributes_access

ALL_FIELDS = [
    ("migration_request_id", "Migration Request ID"),
    ("requested_date", "Requested Date"),
    ("requestor", "Requestor"),
    ("status", "Status"),
    ("project_name", "Project Name"),
    ("migration_type", "Migration Type"),
    ("migration_type_value", "Migration Type Value"),
    ("region", "Region"),
    ("areas", "Areas"),
    ("countries", "Countries"),
    ("area_country_pairs", "Area–Country Pairs"),
    ("default_location_strategies", "Default Location Strategies"),
    ("custom_location_strategies", "Custom Location Strategies"),
    ("location_strategy_custom", "Location Strategy Custom (Y/N)"),
    ("custom_location_strategy_justification", "Custom Strategy Justification"),
    ("custom_approval_file_name", "Approval File Name"),
    ("custom_approval_file_size", "Approval File Size"),
    ("custom_approval_file_type", "Approval File Type"),
    ("function_name", "Function"),
    ("products", "Products"),
    ("proposed_scope", "Proposed Scope"),
    ("language_dependencies", "Language Dependencies"),
    ("fte_number", "FTE Number"),
    ("jl2", "JL2"),
    ("jl3", "JL3"),
    ("jl4", "JL4"),
    ("job_level_total", "Job Level Total"),
    ("risks", "Risks"),
]

LIST_FIELDS = {
    "areas",
    "countries",
    "default_location_strategies",
    "custom_location_strategies",
    "products",
    "language_dependencies",
}

PAIR_FIELD = "area_country_pairs"
BOOL_FIELDS = {"location_strategy_custom"}
INT_FIELDS = {"custom_approval_file_size", "job_level_total"}


def _join_list(values) -> str:
    if not isinstance(values, list):
        return ""
    parts = []
    for value in values:
        text = str(value or "").strip()
        if text:
            parts.append(text)
    return ", ".join(parts)


def _serialize_pairs(pairs) -> str:
    if not isinstance(pairs, list) or not pairs:
        return ""
    try:
        return json.dumps(pairs, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return ""


def _yn(value: bool) -> str:
    return "Y" if value else "N"


def _serialize_row(item: MigrationIntakeSubmission) -> dict:
    return {
        "id": item.id,
        "migration_request_id": item.migration_request_id or "",
        "requested_date": item.requested_date or "",
        "requestor": item.requestor or "",
        "status": item.status or "",
        "project_name": item.project_name or "",
        "migration_type": item.migration_type or "",
        "migration_type_value": item.migration_type_value or "",
        "region": item.region or "",
        "areas": _join_list(item.areas),
        "countries": _join_list(item.countries),
        "area_country_pairs": _serialize_pairs(item.area_country_pairs),
        "default_location_strategies": _join_list(item.default_location_strategies),
        "custom_location_strategies": _join_list(item.custom_location_strategies),
        "location_strategy_custom": _yn(bool(item.location_strategy_custom)),
        "custom_location_strategy_justification": item.custom_location_strategy_justification or "",
        "custom_approval_file_name": item.custom_approval_file_name or "",
        "custom_approval_file_size": (
            "" if item.custom_approval_file_size is None else str(item.custom_approval_file_size)
        ),
        "custom_approval_file_type": item.custom_approval_file_type or "",
        "function_name": item.function_name or "",
        "products": _join_list(item.products),
        "proposed_scope": item.proposed_scope or "",
        "language_dependencies": _join_list(item.language_dependencies),
        "fte_number": item.fte_number or "",
        "jl2": item.jl2 or "0",
        "jl3": item.jl3 or "0",
        "jl4": item.jl4 or "0",
        "job_level_total": str(item.job_level_total or 0),
        "risks": item.risks or "",
    }


@api_view(["GET"])
@require_attributes_access("migration_intake")
def list_migration_intake_submissions(_request):
    rows = [
        _serialize_row(item)
        for item in MigrationIntakeSubmission.objects.all().order_by("-created_at", "id")
    ]
    return Response(
        {
            "count": len(rows),
            "columns": [{"key": key, "label": label} for key, label in ALL_FIELDS],
            "rows": rows,
        }
    )
