from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationTeam
from api.permissions.attributes_access import require_attributes_access

ROLE_VALUES = {value for value, _label in MigrationTeam.ROLE_CHOICES}
MAX_DELETE = 500


@api_view(["GET"])
@require_attributes_access("migration_team")
def list_migration_team(_request):
    rows = [
        {"id": item.id, "role": item.role, "email": item.email}
        for item in MigrationTeam.objects.all()
    ]
    return Response({"count": len(rows), "rows": rows})


@api_view(["POST"])
@require_attributes_access("migration_team")
def save_migration_team(request):
    unique_data = request.data.get("uniqueData")
    if not isinstance(unique_data, list) or not unique_data:
        return Response(
            {"error": "uniqueData must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    valid_rows = []
    errors = []
    for index, item in enumerate(unique_data):
        if not isinstance(item, dict):
            errors.append({"index": index, "error": "Row must be an object."})
            continue

        role = str(item.get("role") or "").strip()
        email = str(item.get("email") or "").strip()
        record_id = item.get("id")
        if role not in ROLE_VALUES:
            errors.append({"index": index, "error": "Role must be Manager or Member."})
            continue
        if not email:
            errors.append({"index": index, "error": "Email is required."})
            continue
        if len(email) > 254:
            errors.append({"index": index, "error": "Email must be 254 characters or fewer."})
            continue
        try:
            validate_email(email)
        except ValidationError:
            errors.append({"index": index, "error": "Enter a valid email address."})
            continue

        if record_id in (None, ""):
            valid_rows.append((None, role, email))
            continue
        try:
            record_id = int(record_id)
        except (TypeError, ValueError):
            errors.append({"index": index, "error": "Record ID must be an integer."})
            continue
        if not MigrationTeam.objects.filter(pk=record_id).exists():
            errors.append({"index": index, "id": record_id, "error": "Record not found."})
            continue
        valid_rows.append((record_id, role, email))

    if errors:
        return Response(
            {"error_count": len(errors), "errors": errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created_count = 0
    updated_count = 0
    with transaction.atomic():
        for record_id, role, email in valid_rows:
            if record_id is None:
                MigrationTeam.objects.create(role=role, email=email)
                created_count += 1
            else:
                record = MigrationTeam.objects.get(pk=record_id)
                record.role = role
                record.email = email
                record.save(update_fields=["role", "email"])
                updated_count += 1

    success_count = created_count + updated_count
    return Response(
        {
            "created_count": created_count,
            "updated_count": updated_count,
            "error_count": len(errors),
            "errors": errors,
        },
        status=status.HTTP_200_OK if success_count else status.HTTP_400_BAD_REQUEST,
    )


@api_view(["DELETE"])
@require_attributes_access("migration_team")
def delete_migration_team(request):
    removed_ids = request.data.get("removedIds")
    if not isinstance(removed_ids, list) or not removed_ids:
        return Response(
            {"error": "removedIds must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(removed_ids) > MAX_DELETE:
        return Response(
            {"error": f"Delete at most {MAX_DELETE} records per request."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        ids = list(dict.fromkeys(int(record_id) for record_id in removed_ids))
        if any(record_id <= 0 for record_id in ids):
            raise ValueError
    except (TypeError, ValueError):
        return Response(
            {"error": "removedIds must contain positive integer IDs."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    found_ids = list(MigrationTeam.objects.filter(pk__in=ids).values_list("pk", flat=True))
    MigrationTeam.objects.filter(pk__in=found_ids).delete()
    found_id_set = set(found_ids)
    errors = [
        {"id": record_id, "error": "Record not found."}
        for record_id in ids
        if record_id not in found_id_set
    ]
    return Response(
        {
            "deleted_count": len(found_ids),
            "error_count": len(errors),
            "errors": errors,
        },
        status=status.HTTP_200_OK if found_ids else status.HTTP_400_BAD_REQUEST,
    )
