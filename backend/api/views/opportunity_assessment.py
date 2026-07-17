"""
Opportunity Assessment API — task-level scoping grid per migration project.
"""

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from django.http import FileResponse

from api.models import FpoMapping, MigrationIntakeSubmission, OpportunityAssessment
from api.services.opportunity_assessment_excel import (
    build_opportunity_template,
    parse_opportunity_workbook,
)
from api.views.fpo_mapping import _build_cascade_tree, _serialize_row as serialize_fpo_row

ALL_FIELDS = [
    ("migration_request_id", "migration_request_id"),
    ("owner", "Owner"),
    ("l1", "L1"),
    ("l2", "L2"),
    ("l3", "L3"),
    ("l4", "L4"),
    ("task_name", "Task Name"),
    ("task_description", "Task Description"),
    ("task_found_in_service_catalog", "Task found in the corresponding Service Catalog?"),
    ("migratable_to_gsc", "Migratable to GSC as per service catalog?"),
    ("upstream", "Upstream (tasks, events, input)"),
    ("downstream", "Downstream (task, events, output)"),
    ("risks_related", "Risks related to the Process/Task"),
    ("complexity", "Complexity (Low, Medium, High)"),
    ("sop_iop_exists", "SOP/IOP Exists?"),
    ("training_time_needed", "Training Time Needed"),
    ("recommended_handoff_duration", "Recommended Handoff Duration"),
    ("task_frequency", "Task Frequency"),
    ("unit_of_measure", "Unit of measure"),
    ("volume", "Volume"),
    ("task_time_per_unit", "Task time per unit"),
    ("fte_calculation", "FTE Calculation"),
]

WRITABLE_FIELDS = [key for key, _label in ALL_FIELDS if key != "migration_request_id"]
CASCADE_FIELD_KEYS = {"l1", "l2", "l3", "l4"}


def _normalize_value(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _serialize_row(item: OpportunityAssessment) -> dict:
    return {
        "id": item.id,
        "migration_request_id": item.migration_request_id,
        "owner": item.owner,
        "l1": item.l1,
        "l2": item.l2,
        "l3": item.l3,
        "l4": item.l4,
        "task_name": item.task_name,
        "task_description": item.task_description,
        "task_found_in_service_catalog": item.task_found_in_service_catalog,
        "migratable_to_gsc": item.migratable_to_gsc,
        "upstream": item.upstream,
        "downstream": item.downstream,
        "risks_related": item.risks_related,
        "complexity": item.complexity,
        "sop_iop_exists": item.sop_iop_exists,
        "training_time_needed": item.training_time_needed,
        "recommended_handoff_duration": item.recommended_handoff_duration,
        "task_frequency": item.task_frequency,
        "unit_of_measure": item.unit_of_measure,
        "volume": item.volume,
        "task_time_per_unit": item.task_time_per_unit,
        "fte_calculation": item.fte_calculation,
    }


def _get_project(project_id: int):
    try:
        return MigrationIntakeSubmission.objects.get(pk=project_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return None


def _build_l1_l4_cascade() -> dict:
    """Build L1→L4 cascade options from FPO mapping dictionary."""
    qs = FpoMapping.objects.all().order_by("id")
    rows = [serialize_fpo_row(item) for item in qs]
    return _build_cascade_tree(rows)


def _is_new_record(record_id) -> bool:
    return record_id is None or record_id == "" or record_id is False


@api_view(["GET"])
def list_opportunity_assessment(request, project_id: int):
    """GET — rows for this project + L1→L4 cascade from FPO mapping."""
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    migration_request_id = project.migration_request_id
    qs = OpportunityAssessment.objects.filter(
        migration_request_id=migration_request_id
    ).order_by("id")
    rows = [_serialize_row(item) for item in qs]

    return Response(
        {
            "project_id": project.id,
            "migration_request_id": migration_request_id,
            "project_name": project.project_name,
            "count": len(rows),
            "columns": [{"key": key, "label": label} for key, label in ALL_FIELDS],
            "cascade_keys": sorted(CASCADE_FIELD_KEYS),
            "cascade": _build_l1_l4_cascade(),
            "rows": rows,
        }
    )


@api_view(["POST"])
def save_opportunity_assessment(request, project_id: int):
    """POST — upsert rows; migration_request_id is always locked to the project."""
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    unique_data = request.data.get("uniqueData")
    if not isinstance(unique_data, list) or len(unique_data) == 0:
        return Response(
            {"error": "uniqueData must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    migration_request_id = project.migration_request_id
    created_ids: list[int] = []
    updated_ids: list[int] = []
    errors: list[dict] = []

    for index, item in enumerate(unique_data):
        if not isinstance(item, dict):
            errors.append({"index": index, "error": "Row must be an object."})
            continue

        record_id = item.get("id")
        payload = {field: _normalize_value(item.get(field)) for field in WRITABLE_FIELDS}
        payload["migration_request_id"] = migration_request_id

        try:
            if _is_new_record(record_id):
                obj = OpportunityAssessment.objects.create(**payload)
                created_ids.append(obj.id)
            else:
                obj = OpportunityAssessment.objects.get(
                    pk=int(record_id),
                    migration_request_id=migration_request_id,
                )
                for field, value in payload.items():
                    setattr(obj, field, value)
                obj.save()
                updated_ids.append(obj.id)
        except OpportunityAssessment.DoesNotExist:
            errors.append({"id": record_id, "error": "Record not found for this project."})
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
            "migration_request_id": migration_request_id,
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
def delete_opportunity_assessment(request, project_id: int):
    """DELETE — remove rows belonging to this project's migration_request_id."""
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    removed_ids = request.data.get("removedIds")
    if not isinstance(removed_ids, list) or len(removed_ids) == 0:
        return Response(
            {"error": "removedIds must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    migration_request_id = project.migration_request_id
    deleted_count = 0
    errors: list[dict] = []

    for raw_id in removed_ids:
        try:
            pk = int(raw_id)
            deleted, _ = OpportunityAssessment.objects.filter(
                pk=pk,
                migration_request_id=migration_request_id,
            ).delete()
            if deleted:
                deleted_count += deleted
            else:
                errors.append({"id": raw_id, "error": "Record not found for this project."})
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


@api_view(["GET"])
def download_opportunity_template(request, project_id: int):
    """
    Download Excel template with:
    - migration_request_id pre-filled for 200 rows
    - L1→L2→L3→L4 cascading dropdowns from fpo_mapping
    """
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        buffer = build_opportunity_template(project.migration_request_id)
    except FileNotFoundError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as exc:  # noqa: BLE001
        return Response(
            {"error": f"Failed to build template: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    filename = f"Opportunity_Assessment_{project.migration_request_id}.xlsx"
    response = FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["X-Migration-Request-Id"] = project.migration_request_id
    return response


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_opportunity_excel(request, project_id: int):
    """
    Bulk upload a filled Opportunity Assessment Excel file.
    Every non-empty row must have migration_request_id matching this project.
    """
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    upload = request.FILES.get("file")
    if not upload:
        return Response(
            {"error": "Please upload an Excel file (.xlsx)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    name = (upload.name or "").lower()
    if not name.endswith((".xlsx", ".xlsm")):
        return Response(
            {"error": "Only .xlsx Excel files are supported."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    migration_request_id = project.migration_request_id

    try:
        parsed = parse_opportunity_workbook(upload, migration_request_id)
    except Exception as exc:  # noqa: BLE001
        return Response(
            {"error": f"Failed to read Excel: {exc}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rows = parsed["rows"]
    row_errors = parsed["errors"]

    if not rows and row_errors:
        return Response(
            {
                "status": "error",
                "migration_request_id": migration_request_id,
                "error": (
                    "No rows imported. All filled rows failed migration_request_id validation. "
                    f"Expected: {migration_request_id}"
                ),
                "imported_count": 0,
                "rejected_count": len(row_errors),
                "errors": row_errors[:50],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not rows:
        return Response(
            {
                "status": "error",
                "migration_request_id": migration_request_id,
                "error": "No data rows found in the Excel file.",
                "imported_count": 0,
                "rejected_count": 0,
                "errors": [],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    objs = [OpportunityAssessment(**row) for row in rows]
    created = OpportunityAssessment.objects.bulk_create(objs, batch_size=200)

    return Response(
        {
            "status": "partial_success" if row_errors else "success",
            "migration_request_id": migration_request_id,
            "imported_count": len(created),
            "rejected_count": len(row_errors),
            "errors": row_errors[:50],
            "message": (
                f"Imported {len(created)} row(s) for {migration_request_id}."
                + (
                    f" Rejected {len(row_errors)} row(s) due to migration_request_id mismatch."
                    if row_errors
                    else ""
                )
            ),
        }
    )
