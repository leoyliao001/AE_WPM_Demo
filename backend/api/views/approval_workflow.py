"""
Approval Workflow API — read-only Handsontable grid.

Data is synced automatically; no create / update / delete endpoints.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import ApprovalWorkflow
from api.permissions.attributes_access import require_attributes_access

ALL_FIELDS = [
    ("migration_request_id", "migration_request_id"),
    ("business_case_submitted_date", "Business case submitted date"),
    ("area_head_approval_trigger_date", "Area Head Approval Trigger Date"),
    ("area_head_comments", "Area Head comments"),
    ("area_head_final_date", "Area Head FinalDate"),
    ("area_head_status", "Area Head Status"),
    ("pmo_review_comment", "PMO Review Comment"),
    ("pmo_review_date", "PMO Review Date"),
    ("pmo_status", "PMO Status"),
    ("bpm_budget_status", "BPM Budget Status"),
    ("bpm_comment", "BPM Comment"),
    ("bpm_review_date", "BPM Review Date"),
    ("fbp_review_date", "FBP Review Date"),
    ("fbp_comment", "FBP Comment"),
    ("fbp_status", "FBP Status"),
    ("wpm_review_date", "WPM Review Date"),
    ("wpm_review_comment", "WPM Review Comment"),
    ("wpm_review_status", "WPM Review Status"),
    ("gsc_head_date", "GSC Head Date"),
    ("gsc_head_comment", "GSC Head Comment"),
    ("gsc_head_status", "GSC Head Status"),
    ("elt_date", "ELT Date"),
    ("elt_comment", "ELT Comment"),
    ("elt_status", "ELT Status"),
]

DATETIME_FIELDS = {
    "business_case_submitted_date",
    "area_head_approval_trigger_date",
    "area_head_final_date",
    "pmo_review_date",
    "bpm_review_date",
    "fbp_review_date",
    "wpm_review_date",
    "gsc_head_date",
    "elt_date",
}


def _format_datetime(value) -> str:
    if value is None:
        return ""
    return value.isoformat(sep=" ", timespec="seconds")


def _serialize_row(item: ApprovalWorkflow) -> dict:
    row = {"id": item.id}
    for key, _label in ALL_FIELDS:
        value = getattr(item, key, None)
        if key in DATETIME_FIELDS:
            row[key] = _format_datetime(value)
        else:
            row[key] = value or ""
    return row


@api_view(["GET"])
@require_attributes_access("approval_workflow")
def list_approval_workflow(_request):
    rows = [
        _serialize_row(item)
        for item in ApprovalWorkflow.objects.all().order_by("-updated_at", "id")
    ]
    return Response(
        {
            "count": len(rows),
            "columns": [{"key": key, "label": label} for key, label in ALL_FIELDS],
            "rows": rows,
            "read_only": True,
        }
    )
