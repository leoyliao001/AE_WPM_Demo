from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import BauControlAgreement, MigrationIntakeSubmission
from api.permissions.attributes_access import (
    get_request_email,
    normalize_email,
    require_attributes_access,
)
from api.services.project_artefacts import project_permissions


FIELD_MAP = {
    "migrationName": "migration_name",
    "product": "product",
    "area": "area",
    "effectiveFrom": "effective_from",
    "areaOwner": "area_owner",
    "gscOwner": "gsc_owner",
    "scopeCovered": "scope_covered",
    "kpiReference": "kpi_reference",
    "reportingSource": "reporting_source",
    "reviewCadence": "review_cadence",
    "performanceOwner": "performance_owner",
    "bauForumChannel": "bau_forum_channel",
    "workingCadence": "working_cadence",
    "areaOperationalContact": "area_operational_contact",
    "gscOperationalContact": "gsc_operational_contact",
    "normalIssueRoute": "normal_issue_route",
    "leadershipRoute": "leadership_route",
    "escalationNote": "escalation_note",
    "areaAccepted": "area_accepted",
    "areaNameRole": "area_name_role",
    "areaAcceptanceDate": "area_acceptance_date",
    "gscAccepted": "gsc_accepted",
    "gscNameRole": "gsc_name_role",
    "gscAcceptanceDate": "gsc_acceptance_date",
}

DATE_FIELDS = {"effectiveFrom", "areaAcceptanceDate", "gscAcceptanceDate"}
BOOL_FIELDS = {"areaAccepted", "gscAccepted"}
TEXT_FIELDS = {"scopeCovered", "escalationNote"}
CHOICE_FIELDS = {
    "reviewCadence": {choice[0] for choice in BauControlAgreement.REVIEW_CADENCE_CHOICES},
    "workingCadence": {choice[0] for choice in BauControlAgreement.WORKING_CADENCE_CHOICES},
}
CHAR_FIELD_MAX_LENGTH = 255
TEXT_FIELD_MAX_LENGTH = 5000


def _serialize_agreement(agreement):
    if agreement is None:
        return None
    result = {
        "id": agreement.pk,
        "status": agreement.status,
        "confirmedAt": agreement.confirmed_at.isoformat() if agreement.confirmed_at else None,
        "confirmedBy": agreement.confirmed_by,
        "createdBy": agreement.created_by,
        "updatedBy": agreement.updated_by,
        "createdAt": agreement.created_at.isoformat(),
        "updatedAt": agreement.updated_at.isoformat(),
    }
    for api_field, model_field in FIELD_MAP.items():
        value = getattr(agreement, model_field)
        result[api_field] = value.isoformat() if model_field in {
            "effective_from",
            "area_acceptance_date",
            "gsc_acceptance_date",
        } and value else value
    return result


def _validate_payload(payload):
    values = {}
    for api_field, model_field in FIELD_MAP.items():
        value = payload.get(api_field)
        if api_field in BOOL_FIELDS:
            if value is None:
                value = False
            if not isinstance(value, bool):
                raise ValueError(f"{api_field} must be true or false.")
        elif api_field in DATE_FIELDS:
            if value in (None, ""):
                value = None
            elif not isinstance(value, str) or parse_date(value) is None:
                raise ValueError(f"Select a valid date for {api_field}.")
            else:
                value = parse_date(value)
        else:
            if value is None:
                value = ""
            if not isinstance(value, str):
                raise ValueError(f"{api_field} must be text.")
            value = value.strip()
            max_length = TEXT_FIELD_MAX_LENGTH if api_field in TEXT_FIELDS else CHAR_FIELD_MAX_LENGTH
            if len(value) > max_length:
                raise ValueError(f"{api_field} must be {max_length} characters or fewer.")
            if api_field in {"reviewCadence", "workingCadence"} and not value:
                value = "Monthly"
            if api_field in CHOICE_FIELDS and value not in CHOICE_FIELDS[api_field]:
                raise ValueError(f"Select a valid {api_field}.")
        values[model_field] = value
    return values


def _action_from_payload(payload):
    action = payload.get("action", "save")
    if not isinstance(action, str) or action not in {"save", "confirm"}:
        raise ValueError("Action must be save or confirm.")
    return action


def _save_agreement(project, values, action, email, agreement=None):
    if action == "confirm" and not (values["area_accepted"] and values["gsc_accepted"]):
        raise ValueError("Area and GSC must both accept before the agreement is confirmed.")

    agreement = agreement or BauControlAgreement(project=project)
    for field, value in values.items():
        setattr(agreement, field, value)
    agreement.status = "confirmed" if action == "confirm" else "draft"
    agreement.confirmed_at = None
    agreement.confirmed_by = ""
    if action == "confirm":
        agreement.confirmed_at = timezone.now()
        agreement.confirmed_by = email
    if not agreement.pk:
        agreement.created_by = email
    agreement.updated_by = email
    agreement.save()
    return agreement


def _project_info(project):
    return {
        "id": project.pk,
        "projectName": project.project_name,
        "migrationRequestId": project.migration_request_id,
        "requestor": project.requestor,
        "products": project.products if isinstance(project.products, list) else [],
        "region": project.region,
    }


@api_view(["GET", "POST"])
def project_bau_controls(request, project_id):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required."}, status=401)

    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if project is None:
        return Response({"error": "Project not found."}, status=404)
    if not project_permissions(project, email, "resources")["view"]:
        return Response(
            {"error": "Only the project requestor, Project Team or users with project access can view BAU Controls."},
            status=403,
        )

    if request.method == "GET":
        agreement = BauControlAgreement.objects.filter(project=project).first()
        return Response({
            "project": _project_info(project),
            "saved": agreement is not None,
            "agreement": _serialize_agreement(agreement),
        })

    if not isinstance(request.data, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    try:
        values = _validate_payload(request.data)
        action = _action_from_payload(request.data)
    except ValueError as error:
        return Response({"error": str(error)}, status=400)

    try:
        with transaction.atomic():
            locked_project = MigrationIntakeSubmission.objects.select_for_update().filter(pk=project.pk).first()
            if locked_project is None:
                return Response({"error": "Project not found."}, status=404)
            agreement = BauControlAgreement.objects.select_for_update().filter(project=locked_project).first()
            is_new = agreement is None
            agreement = _save_agreement(locked_project, values, action, email, agreement)
    except ValueError as error:
        return Response({"error": str(error)}, status=400)
    except IntegrityError:
        return Response({"error": "A BAU Controls record already exists for this project."}, status=409)

    return Response(
        {
            "agreement": _serialize_agreement(agreement),
            "saved": True,
        },
        status=201 if is_new else 200,
    )


def _project_id_from_payload(payload):
    value = payload.get("projectId")
    if type(value) is int:
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise ValueError("Select a valid project.")


def _serialize_admin_agreement(agreement):
    return {
        **_serialize_agreement(agreement),
        "projectId": agreement.project_id,
        "projectName": agreement.project.project_name,
        "migrationRequestId": agreement.project.migration_request_id,
        "requestor": agreement.project.requestor,
    }


@api_view(["GET", "POST"])
@require_attributes_access("bau_control_agreement")
def maintain_bau_controls(request):
    if request.method == "GET":
        rows = [
            _serialize_admin_agreement(agreement)
            for agreement in BauControlAgreement.objects.select_related("project").order_by("-updated_at", "-id")
        ]
        projects = [
            {
                "id": project.pk,
                "projectName": project.project_name,
                "migrationRequestId": project.migration_request_id,
                "requestor": project.requestor,
            }
            for project in MigrationIntakeSubmission.objects.order_by("-id")
        ]
        return Response({"rows": rows, "projects": projects, "count": len(rows)})

    if not isinstance(request.data, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    try:
        project_id = _project_id_from_payload(request.data)
        values = _validate_payload(request.data)
        action = _action_from_payload(request.data)
    except ValueError as error:
        return Response({"error": str(error)}, status=400)
    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if project is None:
        return Response({"error": "Project not found."}, status=404)
    try:
        with transaction.atomic():
            project = MigrationIntakeSubmission.objects.select_for_update().filter(pk=project.pk).first()
            if project is None:
                return Response({"error": "Project not found."}, status=404)
            if BauControlAgreement.objects.filter(project=project).exists():
                return Response({"error": "A BAU Controls record already exists for this project."}, status=409)
            agreement = _save_agreement(project, values, action, request.attributes_email)
    except ValueError as error:
        return Response({"error": str(error)}, status=400)
    except IntegrityError:
        return Response({"error": "A BAU Controls record already exists for this project."}, status=409)
    return Response({"agreement": _serialize_admin_agreement(agreement)}, status=201)


@api_view(["PUT", "DELETE"])
@require_attributes_access("bau_control_agreement")
def maintain_bau_control(request, agreement_id):
    agreement = BauControlAgreement.objects.select_related("project").filter(pk=agreement_id).first()
    if agreement is None:
        return Response({"error": "BAU Controls record not found."}, status=404)
    if request.method == "DELETE":
        agreement.delete()
        return Response({"deleted": True})

    if not isinstance(request.data, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    try:
        project_id = _project_id_from_payload(request.data)
        values = _validate_payload(request.data)
        action = _action_from_payload(request.data)
    except ValueError as error:
        return Response({"error": str(error)}, status=400)
    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if project is None:
        return Response({"error": "Project not found."}, status=404)
    if BauControlAgreement.objects.filter(project=project).exclude(pk=agreement.pk).exists():
        return Response({"error": "A BAU Controls record already exists for this project."}, status=409)
    try:
        with transaction.atomic():
            agreement = BauControlAgreement.objects.select_for_update().filter(pk=agreement_id).first()
            if agreement is None:
                return Response({"error": "BAU Controls record not found."}, status=404)
            agreement.project = project
            agreement = _save_agreement(project, values, action, request.attributes_email, agreement)
    except ValueError as error:
        return Response({"error": str(error)}, status=400)
    return Response({"agreement": _serialize_admin_agreement(agreement)})
