"""
Working Hours API — Handsontable grid (Area / GSC working hours).
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import WorkingHours
from api.permissions.attributes_access import require_attributes_access

ALL_FIELDS = [
    ("area", "area"),
    ("aera_working_hours", "aera_working_hours"),
    ("gsc", "gsc"),
    ("gsc_working_hours", "gsc_working_hours"),
]


def _serialize_row(item: WorkingHours) -> dict:
    return {
        "id": item.id,
        "area": item.area,
        "aera_working_hours": item.aera_working_hours,
        "gsc": item.gsc,
        "gsc_working_hours": item.gsc_working_hours,
    }


@api_view(["GET"])
@require_attributes_access("working_hours")
def list_working_hours(_request):
    rows = [_serialize_row(item) for item in WorkingHours.objects.all().order_by("id")]
    return Response(
        {
            "count": len(rows),
            "columns": [{"key": key, "label": label} for key, label in ALL_FIELDS],
            "rows": rows,
        }
    )
