"""
GSC Site Mapping CRUD — create / update / delete for Handsontable edits.
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import GscSiteMapping
from api.views.gsc_site_mapping import ALL_FIELDS

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
def save_gsc_site_mapping(request):
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
                obj = GscSiteMapping.objects.create(**payload)
                created_ids.append(obj.id)
            else:
                obj = GscSiteMapping.objects.get(pk=int(record_id))
                for field, value in payload.items():
                    setattr(obj, field, value)
                obj.save(update_fields=WRITABLE_FIELDS)
                updated_ids.append(obj.id)
        except GscSiteMapping.DoesNotExist:
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
def delete_gsc_site_mapping(request):
    removed_ids = request.data.get("removedIds")
    if not isinstance(removed_ids, list) or len(removed_ids) == 0:
        return Response(
            {"error": "removedIds must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    deleted_ids: list[int] = []
    errors: list[dict] = []

    for record_id in removed_ids:
        try:
            pk = int(record_id)
            deleted, _ = GscSiteMapping.objects.filter(pk=pk).delete()
            if deleted:
                deleted_ids.append(pk)
            else:
                errors.append({"id": record_id, "error": "Record not found."})
        except (TypeError, ValueError) as exc:
            errors.append({"id": record_id, "error": f"Invalid id: {exc}"})
        except Exception as exc:  # noqa: BLE001
            errors.append({"id": record_id, "error": str(exc)})

    success_count = len(deleted_ids)
    http_status = status.HTTP_200_OK if success_count else status.HTTP_400_BAD_REQUEST

    return Response(
        {
            "status": "success" if not errors else ("partial_success" if success_count else "error"),
            "deleted_count": success_count,
            "deleted_ids": deleted_ids,
            "error_count": len(errors),
            "errors": errors,
        },
        status=http_status,
    )
