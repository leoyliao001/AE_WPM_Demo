"""CRUD for BPM ROFO."""

import re
from datetime import datetime

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import BpmRofo
from api.permissions.attributes_access import require_attributes_access
from api.views.bpm_rofo import ALL_FIELDS

WRITABLE_FIELDS = [key for key, _label in ALL_FIELDS]


def _normalize(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _derive_year(onboarding_month) -> int:
    month_text = _normalize(onboarding_month)
    if not month_text:
        return datetime.now().year

    candidate = month_text
    match = re.search(r"(19|20)\d{2}", candidate)
    if match:
        return int(match.group(0)[:4])

    for fmt in (
        "%Y-%m",
        "%Y/%m",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%Y",
        "%m-%Y",
        "%b-%Y",
        "%B-%Y",
        "%b %Y",
        "%B %Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ):
        try:
            parsed = datetime.strptime(candidate, fmt)
            return parsed.year
        except ValueError:
            continue

    try:
        return int(float(candidate))
    except (TypeError, ValueError):
        return datetime.now().year


def _extract_payload(item: dict) -> dict:
    payload = {field: _normalize(item.get(field)) for field in WRITABLE_FIELDS if field != "year"}
    payload["year"] = _derive_year(payload.get("onboarding_month"))
    return payload


def _is_new_record(record_id):
    return record_id is None or record_id == "" or record_id is False


@api_view(["POST"])
@require_attributes_access("bpm_rofo")
def save_bpm_rofo(request):
    unique_data = request.data.get("uniqueData")
    if not isinstance(unique_data, list) or len(unique_data) == 0:
        return Response({"error": "uniqueData must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

    created_ids = []
    updated_ids = []
    errors = []
    for index, item in enumerate(unique_data):
        if not isinstance(item, dict):
            errors.append({"index": index, "error": "Row must be an object."})
            continue
        record_id = item.get("id")
        payload = _extract_payload(item)
        if not payload.get("project_name"):
            errors.append({"index": index, "error": "Project name is required."})
            continue
        try:
            if _is_new_record(record_id):
                obj = BpmRofo.objects.create(**payload)
                created_ids.append(obj.id)
            else:
                obj = BpmRofo.objects.get(pk=int(record_id))
                for field, value in payload.items():
                    setattr(obj, field, value)
                obj.save(update_fields=[field for field in WRITABLE_FIELDS if field != "id"]) 
                updated_ids.append(obj.id)
        except BpmRofo.DoesNotExist:
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
@require_attributes_access("bpm_rofo")
def delete_bpm_rofo(request):
    removed_ids = request.data.get("removedIds")
    if not isinstance(removed_ids, list) or len(removed_ids) == 0:
        return Response({"error": "removedIds must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

    deleted_ids = []
    errors = []
    for record_id in removed_ids:
        try:
            pk = int(record_id)
            deleted, _ = BpmRofo.objects.filter(pk=pk).delete()
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
