"""
Migration Intake submissions CRUD — create / update / delete for Handsontable edits.

Endpoints:
  POST   /api/migration-intake-submissions/data/
  DELETE /api/migration-intake-submissions/data/delete/
"""

from __future__ import annotations

import json

from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationIntakeSubmission
from api.permissions.attributes_access import require_attributes_access
from api.views.migration_intake_submissions import (
    ALL_FIELDS,
    BOOL_FIELDS,
    LIST_FIELDS,
    PAIR_FIELD,
)

WRITABLE_FIELDS = [key for key, _label in ALL_FIELDS]


def _normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_bool(value) -> bool:
    text = str(value or "").strip().lower()
    return text in {"1", "true", "y", "yes"}


def _parse_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    # Prefer JSON array when pasted; otherwise comma/semicolon separated.
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    parts = []
    for chunk in text.replace(";", ",").split(","):
        item = chunk.strip()
        if item:
            parts.append(item)
    return parts


def _parse_pairs(value) -> list[dict]:
    if isinstance(value, list):
        raw = value
    else:
        text = _normalize_text(value)
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                raw = parsed if isinstance(parsed, list) else []
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(
                    "area_country_pairs must be JSON like "
                    '[{"area":"X","country":"Y"}] or "Area|Country; Area2|Country2".'
                ) from exc
        else:
            raw = []
            for chunk in text.replace(",", ";").split(";"):
                part = chunk.strip()
                if not part:
                    continue
                if "|" not in part:
                    raise ValueError(
                        f"Invalid area–country pair '{part}'. Use Area|Country."
                    )
                area, country = part.split("|", 1)
                raw.append({"area": area.strip(), "country": country.strip()})

    result = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        area = str(item.get("area") or "").strip()
        country = str(item.get("country") or "").strip()
        if not area or not country:
            continue
        key = (area.lower(), country.lower())
        if key in seen:
            continue
        seen.add(key)
        result.append({"area": area, "country": country})
    return result


def _parse_int(value, *, allow_null: bool = False):
    text = _normalize_text(value)
    if text == "":
        return None if allow_null else 0
    try:
        return int(float(text))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid number: {value}") from exc


def _jl_total(jl2: str, jl3: str, jl4: str, explicit) -> int:
    if _normalize_text(explicit) != "":
        return max(0, _parse_int(explicit))
    total = 0
    for value in (jl2, jl3, jl4):
        try:
            total += max(0, int(float(str(value or "0").strip() or "0")))
        except (TypeError, ValueError):
            continue
    return total


def _extract_payload(item: dict) -> dict:
    payload: dict = {}
    for field in WRITABLE_FIELDS:
        raw = item.get(field)
        if field in LIST_FIELDS:
            payload[field] = _parse_list(raw)
        elif field == PAIR_FIELD:
            payload[field] = _parse_pairs(raw)
        elif field in BOOL_FIELDS:
            payload[field] = _parse_bool(raw)
        elif field == "custom_approval_file_size":
            payload[field] = _parse_int(raw, allow_null=True)
        elif field == "job_level_total":
            continue
        else:
            payload[field] = _normalize_text(raw)

    payload["job_level_total"] = _jl_total(
        payload.get("jl2", "0"),
        payload.get("jl3", "0"),
        payload.get("jl4", "0"),
        item.get("job_level_total"),
    )
    if not payload.get("status"):
        payload["status"] = "new"
    for jl_key in ("jl2", "jl3", "jl4"):
        if not payload.get(jl_key):
            payload[jl_key] = "0"
    return payload


def _is_new_record(record_id) -> bool:
    return record_id is None or record_id == "" or record_id is False


@api_view(["POST"])
@require_attributes_access("migration_intake")
def save_migration_intake_submissions(request):
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
        try:
            payload = _extract_payload(item)
        except ValueError as exc:
            errors.append({"index": index, "id": record_id, "error": str(exc)})
            continue

        if not payload.get("migration_request_id"):
            errors.append(
                {
                    "index": index,
                    "id": record_id,
                    "error": "Migration Request ID is required.",
                }
            )
            continue
        if not payload.get("project_name"):
            errors.append(
                {
                    "index": index,
                    "id": record_id,
                    "error": "Project Name is required.",
                }
            )
            continue

        try:
            if _is_new_record(record_id):
                obj = MigrationIntakeSubmission.objects.create(**payload)
                created_ids.append(obj.id)
            else:
                obj = MigrationIntakeSubmission.objects.get(pk=int(record_id))
                for field, value in payload.items():
                    setattr(obj, field, value)
                obj.save(update_fields=WRITABLE_FIELDS)
                updated_ids.append(obj.id)
        except MigrationIntakeSubmission.DoesNotExist:
            errors.append({"id": record_id, "error": "Record not found."})
        except IntegrityError:
            errors.append(
                {
                    "id": record_id,
                    "error": (
                        f"Duplicate Migration Request ID: "
                        f"{payload.get('migration_request_id')}"
                    ),
                }
            )
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
@require_attributes_access("migration_intake")
def delete_migration_intake_submissions(request):
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
            deleted, _ = MigrationIntakeSubmission.objects.filter(pk=pk).delete()
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
