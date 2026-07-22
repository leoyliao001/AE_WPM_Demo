"""
GSC Site Mapping API — Region / Area / Supporting GSC Sites / All options.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import GscSiteMapping

ALL_FIELDS = [
    ("region", "Region"),
    ("area", "Area"),
    ("supporting_gsc_sites", "Supporting GSC Sites"),
    ("all_options", "All options"),
]


def _serialize_row(item: GscSiteMapping) -> dict:
    return {
        "id": item.id,
        "region": item.region,
        "area": item.area,
        "supporting_gsc_sites": item.supporting_gsc_sites,
        "all_options": item.all_options,
    }


@api_view(["GET"])
def list_gsc_site_mapping(_request):
    rows = [_serialize_row(item) for item in GscSiteMapping.objects.all().order_by("id")]
    return Response(
        {
            "count": len(rows),
            "columns": [{"key": key, "label": label} for key, label in ALL_FIELDS],
            "rows": rows,
        }
    )
