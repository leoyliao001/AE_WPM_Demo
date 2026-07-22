"""
Product Ownership API — Handsontable grid (Product / Manager / Region / Migration Manager).
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import ProductOwnership

ALL_FIELDS = [
    ("product", "Product"),
    ("manager", "Manager"),
    ("region", "Region"),
    ("migration_manager", "Migration Manager"),
]


def _serialize_row(item: ProductOwnership) -> dict:
    return {
        "id": item.id,
        "product": item.product,
        "manager": item.manager,
        "region": item.region,
        "migration_manager": item.migration_manager,
    }


@api_view(["GET"])
def list_product_ownership(_request):
    rows = [_serialize_row(item) for item in ProductOwnership.objects.all().order_by("id")]
    return Response(
        {
            "count": len(rows),
            "columns": [{"key": key, "label": label} for key, label in ALL_FIELDS],
            "rows": rows,
        }
    )
