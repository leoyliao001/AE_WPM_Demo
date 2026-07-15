"""
FPO Mapping CRUD — create / update / delete for Handsontable edits.

Endpoints:
  POST   /api/fpo-mapping/data/   body: { "uniqueData": [ {...}, ... ] }
  DELETE /api/fpo-mapping/data/   body: { "removedIds": [1, 2, ...] }
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import FpoMapping
from api.views.fpo_mapping import ALL_FIELDS

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
def save_fpo_mapping(request):
    """
    Upsert FPO mapping rows from Handsontable.

    - Missing / null / empty ``id`` → INSERT
    - Numeric ``id`` → UPDATE that row
    """
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
                obj = FpoMapping.objects.create(**payload)
                created_ids.append(obj.id)
            else:
                obj = FpoMapping.objects.get(pk=int(record_id))
                for field, value in payload.items():
                    setattr(obj, field, value)
                obj.save(update_fields=WRITABLE_FIELDS)
                updated_ids.append(obj.id)
        except FpoMapping.DoesNotExist:
            errors.append({"id": record_id, "error": "Record not found."})
        except (TypeError, ValueError) as exc:
            errors.append({"id": record_id, "error": f"Invalid id: {exc}"})
        except Exception as exc:  # noqa: BLE001 — surface per-row failures to UI
            errors.append({"id": record_id, "error": str(exc)})

    success_count = len(created_ids) + len(updated_ids)
    result_status = "success" if not errors else ("partial_success" if success_count else "error")
    http_status = (
        status.HTTP_200_OK
        if success_count
        else status.HTTP_400_BAD_REQUEST
    )

    return Response(
        {
            "status": result_status,
            "success_count": success_count,
            "created_count": len(created_ids),
            "updated_count": len(updated_ids),
            "created_ids": created_ids,
            "updated_ids": updated_ids,
            "error_count": len(errors),
            "errors": errors,
        },
        status=http_status,
    )


@api_view(["DELETE"])
def delete_fpo_mapping(request):
    """Hard-delete FPO mapping rows by primary key ids."""
    removed_ids = request.data.get("removedIds")
    if not isinstance(removed_ids, list) or len(removed_ids) == 0:
        return Response(
            {"error": "removedIds must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    deleted_count = 0
    errors: list[dict] = []

    for raw_id in removed_ids:
        try:
            pk = int(raw_id)
            deleted, _ = FpoMapping.objects.filter(pk=pk).delete()
            if deleted:
                deleted_count += deleted
            else:
                errors.append({"id": raw_id, "error": "Record not found."})
        except (TypeError, ValueError) as exc:
            errors.append({"id": raw_id, "error": f"Invalid id: {exc}"})
        except Exception as exc:  # noqa: BLE001
            errors.append({"id": raw_id, "error": str(exc)})

    return Response(
        {
            "status": True,
            "deleted_count": deleted_count,
            "error_count": len(errors),
            "errors": errors,
        }
    )
