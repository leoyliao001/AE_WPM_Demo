"""
Product Ownership API — Handsontable grid (Region / Area / Migration Manager).
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import ProductOwnership
from api.permissions.attributes_access import require_attributes_access

ALL_FIELDS = [
    ("region", "Region"),
    ("area", "Area"),
    ("migration_manager", "Migration Manager"),
]


def _serialize_row(item: ProductOwnership) -> dict:
    return {
        "id": item.id,
        "region": item.region,
        "area": item.area,
        "migration_manager": item.migration_manager,
    }


@api_view(["GET"])
@require_attributes_access("product_ownership")
def list_product_ownership(_request):
    rows = [_serialize_row(item) for item in ProductOwnership.objects.all().order_by("id")]
    return Response(
        {
            "count": len(rows),
            "columns": [{"key": key, "label": label} for key, label in ALL_FIELDS],
            "rows": rows,
        }
    )
