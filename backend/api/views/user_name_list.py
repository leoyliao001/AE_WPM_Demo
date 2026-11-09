from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import UserNameList
from api.permissions.attributes_access import require_attributes_access

MAX_RESULTS = 500


@api_view(["GET"])
@require_attributes_access("user_name_list")
def list_user_names(request):
    display_name = str(request.query_params.get("display_name", "")).strip()
    mail = str(request.query_params.get("mail", "")).strip()
    if not display_name and not mail:
        return Response(
            {"error": "Enter a display name or email to search."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    queryset = UserNameList.objects.all()
    if display_name:
        queryset = queryset.filter(display_name__icontains=display_name)
    if mail:
        queryset = queryset.filter(mail__icontains=mail)

    count = queryset.count()
    rows = [
        {"id": item.id, "display_name": item.display_name, "mail": item.mail}
        for item in queryset.order_by("display_name", "id")[:MAX_RESULTS]
    ]
    return Response({"count": count, "rows": rows, "has_more": count > MAX_RESULTS})


@api_view(["POST"])
@require_attributes_access("user_name_list")
def save_user_names(request):
    unique_data = request.data.get("uniqueData")
    if not isinstance(unique_data, list) or not unique_data:
        return Response(
            {"error": "uniqueData must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created_ids = []
    updated_ids = []
    saved_records = []
    errors = []
    with transaction.atomic():
        for index, item in enumerate(unique_data):
            if not isinstance(item, dict):
                errors.append({"index": index, "error": "Row must be an object."})
                continue

            display_name = str(item.get("display_name") or "").strip()
            mail = str(item.get("mail") or "").strip()
            record_id = item.get("id")
            if not display_name:
                errors.append({"index": index, "error": "Display name is required."})
                continue
            if len(display_name) > 255 or len(mail) > 255:
                errors.append({"index": index, "error": "Fields must be 255 characters or fewer."})
                continue

            try:
                with transaction.atomic():
                    if record_id in (None, ""):
                        record = UserNameList.objects.create(display_name=display_name, mail=mail)
                        created_ids.append(record.id)
                    else:
                        record = UserNameList.objects.get(pk=int(record_id))
                        record.display_name = display_name
                        record.mail = mail
                        record.save(update_fields=["display_name", "mail"])
                        updated_ids.append(record.id)
                saved_records.append({"index": index, "id": record.id})
            except (UserNameList.DoesNotExist, TypeError, ValueError):
                errors.append({"index": index, "id": record_id, "error": "Record not found."})
            except Exception as exc:  # noqa: BLE001
                errors.append({"index": index, "id": record_id, "error": str(exc)})

    success_count = len(created_ids) + len(updated_ids)
    result_state = "success" if not errors else "partial_success" if success_count else "error"
    return Response(
        {
            "status": result_state,
            "created_count": len(created_ids),
            "updated_count": len(updated_ids),
            "saved_records": saved_records,
            "error_count": len(errors),
            "errors": errors,
        },
        status=status.HTTP_200_OK if success_count else status.HTTP_400_BAD_REQUEST,
    )


@api_view(["DELETE"])
@require_attributes_access("user_name_list")
def delete_user_names(request):
    removed_ids = request.data.get("removedIds")
    if not isinstance(removed_ids, list) or not removed_ids:
        return Response(
            {"error": "removedIds must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(removed_ids) > MAX_RESULTS:
        return Response(
            {"error": f"Delete at most {MAX_RESULTS} records per request."},
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

    found_ids = list(UserNameList.objects.filter(pk__in=ids).values_list("pk", flat=True))
    UserNameList.objects.filter(pk__in=found_ids).delete()
    found_id_set = set(found_ids)
    errors = [
        {"id": record_id, "error": "Record not found."}
        for record_id in ids
        if record_id not in found_id_set
    ]
    return Response(
        {
            "status": "success" if not errors else "partial_success" if found_ids else "error",
            "deleted_count": len(found_ids),
            "deleted_ids": found_ids,
            "error_count": len(errors),
            "errors": errors,
        },
        status=status.HTTP_200_OK if found_ids else status.HTTP_400_BAD_REQUEST,
    )