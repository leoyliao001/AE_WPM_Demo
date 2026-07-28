"""
Service Catalogue API — Handsontable grid (Product / L1–L4 / ownership).
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import ServiceCatalogue
from api.permissions.attributes_access import require_attributes_access

ALL_FIELDS = [
    ("catalogue", "Catalogue"),
    ("product", "Product"),
    ("l1", "L1: Domain"),
    ("l2", "L2: Process Capability"),
    ("l3", "L3: Processes"),
    ("l4", "L4: Activities"),
    ("current_ownership", "Current Ownership"),
    ("customer", "Customer"),
]


def _serialize_row(item: ServiceCatalogue) -> dict:
    return {
        "id": item.id,
        "catalogue": item.catalogue,
        "product": item.product,
        "l1": item.l1,
        "l2": item.l2,
        "l3": item.l3,
        "l4": item.l4,
        "current_ownership": item.current_ownership,
        "customer": item.customer,
    }


@api_view(["GET"])
@require_attributes_access("service_catalogue")
def list_service_catalogue(_request):
    rows = [_serialize_row(item) for item in ServiceCatalogue.objects.all().order_by("id")]
    return Response(
        {
            "count": len(rows),
            "columns": [{"key": key, "label": label} for key, label in ALL_FIELDS],
            "rows": rows,
        }
    )
