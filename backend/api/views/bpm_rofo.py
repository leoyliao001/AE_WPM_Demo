"""BPM ROFO API — editable planning table."""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import BpmRofo
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
    ("rofo_value", "ROFO Value"),
    ("notes", "Notes"),
]


def _serialize_row(item: BpmRofo) -> dict:
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
        "rofo_value": item.rofo_value or item.positions_to_be_offshored_in_gsc,
        "notes": item.notes,
    }


@api_view(["GET"])
@require_attributes_access("bpm_rofo")
def list_bpm_rofo(request):
    year = (request.GET.get("year") or "").strip()
    qs = BpmRofo.objects.all()
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
