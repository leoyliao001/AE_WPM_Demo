from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import BaselineKpiRecord, MigrationIntakeSubmission
from api.permissions.attributes_access import require_attributes_access


def _serialize_record(record):
    project = record.project
    return {
        "id": record.pk,
        "projectId": project.pk,
        "migrationRequestId": project.migration_request_id,
        "projectName": project.project_name,
        "state": record.state,
        "revision": record.revision,
        "updatedBy": record.updated_by,
        "updatedAt": record.updated_at.isoformat(),
    }


@api_view(["GET", "POST"])
@require_attributes_access("baseline_kpis")
def baseline_kpi_records(request):
    if request.method == "GET":
        rows = [
            _serialize_record(record)
            for record in BaselineKpiRecord.objects.select_related("project").order_by(
                "project__migration_request_id"
            )
        ]
        projects = [
            {
                "id": project.pk,
                "migrationRequestId": project.migration_request_id,
                "projectName": project.project_name,
            }
            for project in MigrationIntakeSubmission.objects.order_by(
                "migration_request_id"
            )
        ]
        return Response({"rows": rows, "projects": projects})

    state = request.data.get("state")
    if not isinstance(state, dict):
        return Response(
            {"error": "state must be a JSON object."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        project_id = int(request.data.get("projectId"))
    except (TypeError, ValueError):
        return Response(
            {"error": "Select a valid migration project."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():
            project = MigrationIntakeSubmission.objects.select_for_update().get(
                pk=project_id
            )
            if BaselineKpiRecord.objects.filter(project=project).exists():
                return Response(
                    {"error": "This project already has a Baseline & KPI record."},
                    status=status.HTTP_409_CONFLICT,
                )
            record = BaselineKpiRecord.objects.create(
                project=project,
                state=state,
                revision=1,
                updated_by=request.attributes_email,
            )
    except MigrationIntakeSubmission.DoesNotExist:
        return Response(
            {"error": "Migration project not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except IntegrityError:
        return Response(
            {"error": "This project already has a Baseline & KPI record."},
            status=status.HTTP_409_CONFLICT,
        )
    return Response(_serialize_record(record), status=status.HTTP_201_CREATED)


@api_view(["PUT", "DELETE"])
@require_attributes_access("baseline_kpis")
def baseline_kpi_record_detail(request, record_id):
    if request.method == "DELETE":
        deleted, _ = BaselineKpiRecord.objects.filter(pk=record_id).delete()
        if not deleted:
            return Response(
                {"error": "Baseline & KPI record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    state = request.data.get("state")
    if not isinstance(state, dict):
        return Response(
            {"error": "state must be a JSON object."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        revision = int(request.data.get("revision"))
    except (TypeError, ValueError):
        return Response(
            {"error": "A valid revision is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        record = BaselineKpiRecord.objects.select_for_update().select_related(
            "project"
        ).filter(pk=record_id).first()
        if record is None:
            return Response(
                {"error": "Baseline & KPI record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if revision != record.revision:
            return Response(
                {"error": "This record changed since it was loaded. Reload before saving."},
                status=status.HTTP_409_CONFLICT,
            )
        record.state = state
        record.revision += 1
        record.updated_by = request.attributes_email
        record.save(update_fields=["state", "revision", "updated_by", "updated_at"])
    return Response(_serialize_record(record))
