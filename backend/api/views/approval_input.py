"""
Approval Input — list view for Handsontable grid.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import ApprovalInput
from api.permissions.attributes_access import require_attributes_access

ALL_FIELDS = [
    ("activity_function", "Activity Function"),
    ("product", "Product"),
    ("area_head", "Area Head"),
    ("pmo", "PMO"),
    ("bpm", "BPM"),
    ("fbp", "FBP"),
    ("wpm", "WPM"),
    ("elt", "ELT"),
    ("gsc_head", "GSC Head"),
]


def _serialize_row(item: ApprovalInput) -> dict:
    return {
        "id": item.id,
        "activity_function": item.activity_function,
        "product": item.product,
        "area_head": item.area_head,
        "pmo": item.pmo,
        "bpm": item.bpm,
        "fbp": item.fbp,
        "wpm": item.wpm,
        "elt": item.elt,
        "gsc_head": item.gsc_head,
    }


@api_view(["GET"])
@require_attributes_access("input_for_approval")
def list_approval_input(_request):
    rows = [_serialize_row(item) for item in ApprovalInput.objects.all().order_by("id")]
    return Response({
        "columns": [{"key": k, "label": v} for k, v in ALL_FIELDS],
        "rows": rows,
    })
