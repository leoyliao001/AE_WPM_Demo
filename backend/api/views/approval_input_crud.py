"""
Approval Input CRUD — create / update / delete for Handsontable edits.

Endpoints:
  POST   /api/input-for-approval/data/         body: { "uniqueData": [ {...}, ... ] }
  DELETE /api/input-for-approval/data/delete/  body: { "removedIds": [1, 2, ...] }
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import ApprovalInput
from api.permissions.attributes_access import require_attributes_access
from api.views.approval_input import ALL_FIELDS

WRITABLE_FIELDS = [key for key, _label in ALL_FIELDS]


def _normalize_value(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _extract_payload(item: dict) -> dict:
    return {field: _normalize_value(item.get(field)) for field in WRITABLE_FIELDS}


def _is_new_record(record_id) -> bool:
    return record_id is None or record_id == "" or record_id is False


@api_view(["POST"])
@require_attributes_access("input_for_approval")
def save_approval_input(request):
    unique_data = request.data.get("uniqueData")
    if not isinstance(unique_data, list) or len(unique_data) == 0:
        return Response(
            {"error": "uniqueData must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created_ids: list[int] = []
    updated_ids: list[int] = []
    errors: list[dict] = []

    for index, item in enumerate(unique_data):
        if not isinstance(item, dict):
            errors.append({"index": index, "error": "Row must be an object."})
            continue

        record_id = item.get("id")
        payload = _extract_payload(item)

        try:
            if _is_new_record(record_id):
                obj = ApprovalInput.objects.create(**payload)
                created_ids.append(obj.id)
            else:
                obj = ApprovalInput.objects.get(pk=int(record_id))
                for field, value in payload.items():
                    setattr(obj, field, value)
                obj.save(update_fields=WRITABLE_FIELDS)
                updated_ids.append(obj.id)
        except ApprovalInput.DoesNotExist:
            errors.append({"id": record_id, "error": "Record not found."})
        except (TypeError, ValueError) as exc:
            errors.append({"id": record_id, "error": f"Invalid id: {exc}"})
        except Exception as exc:  # noqa: BLE001
            errors.append({"id": record_id, "error": str(exc)})

    success_count = len(created_ids) + len(updated_ids)
    result_status = "success" if not errors else ("partial_success" if success_count else "error")
    http_status = status.HTTP_200_OK if success_count else status.HTTP_400_BAD_REQUEST

    return Response(
        {
            "status": result_status,
            "success_count": success_count,
            "created_ids": created_ids,
            "updated_ids": updated_ids,
            "errors": errors,
        },
        status=http_status,
    )


@api_view(["DELETE"])
@require_attributes_access("input_for_approval")
def delete_approval_input(request):
    removed_ids = request.data.get("removedIds")
    if not isinstance(removed_ids, list) or len(removed_ids) == 0:
        return Response(
            {"error": "removedIds must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        ids = [int(i) for i in removed_ids]
    except (TypeError, ValueError):
        return Response({"error": "All ids must be integers."}, status=status.HTTP_400_BAD_REQUEST)

    deleted_count, _ = ApprovalInput.objects.filter(pk__in=ids).delete()
    return Response({"status": "success", "deleted_count": deleted_count})
