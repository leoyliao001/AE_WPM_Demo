"""
Project Attributes Access CRUD for Handsontable edits.
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import ProjectAttributesAccess
from api.permissions.attributes_access import normalize_email, require_attributes_access
from api.views.project_attributes_access import BOOL_FIELDS

WRITABLE_FIELDS = [
    "email",
    "is_super_admin",
    "fpo_mapping",
    "product_ownership",
    "gsc_site_mapping",
    "access_control",
]


def _parse_bool(value) -> bool:
    text = str(value or "").strip().lower()
    return text in {"1", "true", "y", "yes"}


def _extract_payload(item: dict) -> dict:
    payload = {}
    for field in WRITABLE_FIELDS:
        raw = item.get(field)
        if field == "email":
            payload[field] = normalize_email(raw)
        elif field in BOOL_FIELDS:
            payload[field] = _parse_bool(raw)
        else:
            payload[field] = str(raw or "").strip()
    if payload.get("is_super_admin"):
        payload["fpo_mapping"] = True
        payload["product_ownership"] = True
        payload["gsc_site_mapping"] = True
        payload["access_control"] = True
    return payload


def _is_new_record(record_id) -> bool:
    return record_id is None or record_id == "" or record_id is False


@api_view(["POST"])
@require_attributes_access("access_control")
def save_project_attributes_access(request):
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
        if not payload.get("email"):
            errors.append({"index": index, "error": "Email is required."})
            continue

        try:
            if _is_new_record(record_id):
                obj = ProjectAttributesAccess.objects.create(**payload)
                created_ids.append(obj.id)
            else:
                obj = ProjectAttributesAccess.objects.get(pk=int(record_id))
                for field, value in payload.items():
                    setattr(obj, field, value)
                obj.save(update_fields=WRITABLE_FIELDS)
                updated_ids.append(obj.id)
        except ProjectAttributesAccess.DoesNotExist:
            errors.append({"id": record_id, "error": "Record not found."})
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
@require_attributes_access("access_control")
def delete_project_attributes_access(request):
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
            deleted, _ = ProjectAttributesAccess.objects.filter(pk=pk).delete()
            if deleted:
                deleted_ids.append(pk)
            else:
                errors.append({"id": record_id, "error": "Record not found."})
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
