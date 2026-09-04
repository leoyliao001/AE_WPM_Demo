"""BPM Actual API — editable actuals table."""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import BpmActual
from api.permissions.attributes_access import require_attributes_access

ALL_FIELDS = [
    ("project_name", "Project Name"),
    ("product", "Product"),
    ("region", "Region"),
    ("area", "Area"),
    ("onboarding_month", "Onboarding Month"),
    ("year", "Year"),
    ("bpm_owner", "BPM Owner"),
    ("positions_to_be_offshored_in_gsc", "Positions to be Offshored in GSC"),
    ("part_not_part_of_rofo", "Part/Not part of ROFO"),
    ("actual_value", "Actual Value"),
    ("notes", "Notes"),
]


def _serialize_row(item: BpmActual) -> dict:
    return {
        "id": item.id,
        "project_name": item.project_name,
        "product": item.product,
        "region": item.region,
        "area": item.area,
        "onboarding_month": item.onboarding_month,
        "year": item.year,
        "bpm_owner": item.bpm_owner,
        "positions_to_be_offshored_in_gsc": item.positions_to_be_offshored_in_gsc,
        "part_not_part_of_rofo": item.part_not_part_of_rofo,
        "actual_value": item.actual_value or item.positions_to_be_offshored_in_gsc,
        "notes": item.notes,
    }


@api_view(["GET"])
@require_attributes_access("bpm_actual")
def list_bpm_actual(request):
    year = (request.GET.get("year") or "").strip()
    qs = BpmActual.objects.all()
    if year:
        try:
            qs = qs.filter(year=int(year))
        except ValueError:
            qs = qs.none()
    rows = [_serialize_row(item) for item in qs.order_by("-year", "project_name", "id")]
    return Response({
        "count": len(rows),
        "columns": [{"key": key, "label": label} for key, label in ALL_FIELDS],
        "rows": rows,
    })
