"""BPM Actual API — editable actuals table."""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import BpmActual
from api.permissions.attributes_access import require_attributes_access

ALL_FIELDS = [
    ("status", "Status"),
    ("country", "Country"),
    ("region", "Region"),
    ("area", "Area"),
    ("gsc_site", "GSC Site to be Offshored"),
    ("function", "Function"),
    ("function_id_description", "Function ID + Description"),
    ("product", "Product"),
    ("cost_center", "Cost Center"),
    ("pid", "PID"),
    ("project_name", "Project Name"),
    ("part_not_part_of_rofo", "Part/Not part of ROFO"),
    ("gsc_leader", "GSC Leaders"),
    ("gsc1_leader", "GSC-1 Leaders"),
    ("bpm_owner", "BPM Owner"),
    ("bu", "BU"),
    ("frontline_staff_cost_per_fte", "Frontline Staff Cost per FTE"),
    ("gsc_staff_cost_per_fte", "GSC Staff Cost per FTE"),
    ("project_cost", "Project Cost"),
    ("x_column", "X"),
    ("base_pids", "Base PIDs"),
    ("positions_to_be_offshored_in_gsc", "Positions to be Offshored in GSC"),
    ("positions_to_be_released_in_frontline", "Positions to be Released in Frontline"),
    ("actual_value", "Actual Value"),
    ("year", "Year"),
    ("onboarding_month", "Onboarding Month"),
    ("notes", "Notes"),
]


def _serialize_row(item: BpmActual) -> dict:
    return {
        "id": item.id,
        "status": item.status,
        "country": item.country,
        "region": item.region,
        "area": item.area,
        "gsc_site": item.gsc_site,
        "function": item.function,
        "function_id_description": item.function_id_description,
        "product": item.product,
        "cost_center": item.cost_center,
        "pid": item.pid,
        "project_name": item.project_name,
        "part_not_part_of_rofo": item.part_not_part_of_rofo,
        "gsc_leader": item.gsc_leader,
        "gsc1_leader": item.gsc1_leader,
        "bpm_owner": item.bpm_owner,
        "bu": item.bu,
        "frontline_staff_cost_per_fte": item.frontline_staff_cost_per_fte,
        "gsc_staff_cost_per_fte": item.gsc_staff_cost_per_fte,
        "project_cost": item.project_cost,
        "x_column": item.x_column,
        "base_pids": item.base_pids,
        "positions_to_be_offshored_in_gsc": item.positions_to_be_offshored_in_gsc,
        "positions_to_be_released_in_frontline": item.positions_to_be_released_in_frontline,
        "actual_value": item.actual_value or item.positions_to_be_offshored_in_gsc,
        "year": item.year,
        "onboarding_month": item.onboarding_month,
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
