from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationIntakeSubmission, ProjectCharter
from api.permissions.attributes_access import can_access_table, get_request_email, normalize_email, require_attributes_access
from api.services.project_charter import DELIVERABLES, build_charter_sources


def _authorize(request, project):
    email = normalize_email(get_request_email(request))
    if not email:
        return "", Response({"error": "Sign in required. Missing SSO email."}, status=401)
    if email != normalize_email(project.requestor) and not can_access_table(email, "project_charter"):
        return "", Response({"error": "Only the project requestor or a user with Project Charter access can manage this charter."}, status=403)
    return email, None


def _serialize(project, charter):
    sources, fingerprint = build_charter_sources(project)
    return {
        "projectId": project.id, "projectName": project.project_name,
        "migrationRequestId": project.migration_request_id,
        "saved": charter is not None, "status": "draft",
        "revision": charter.revision if charter else 0,
        "vision": charter.vision if charter else sources["draftVision"],
        "deliverableNotes": charter.deliverable_notes if charter else {},
        "extraSuccessCriteria": charter.extra_success_criteria if charter else [],
        "updatedAt": charter.updated_at.isoformat() if charter else "",
        "updatedBy": charter.updated_by if charter else "",
        "auditLog": charter.audit_log if charter else [],
        "sourceUpdated": bool(charter and charter.source_fingerprint != fingerprint),
        "sources": sources,
    }


@api_view(["GET"])
def get_project_charter(request, project_id):
    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if project is None:
        return Response({"error": "Project not found."}, status=404)
    _, denied = _authorize(request, project)
    if denied is not None:
        return denied
    return Response(_serialize(project, ProjectCharter.objects.filter(project=project).first()))


def _text(value, label, limit):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(f"{label} must be text of at most {limit} characters.")
    return value.strip()


@api_view(["POST"])
def save_project_charter(request, project_id):
    if not isinstance(request.data, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    with transaction.atomic():
        project = MigrationIntakeSubmission.objects.select_for_update().filter(pk=project_id).first()
        if project is None:
            return Response({"error": "Project not found."}, status=404)
        email, denied = _authorize(request, project)
        if denied is not None:
            return denied
        charter = ProjectCharter.objects.filter(project=project).first()
        revision = request.data.get("revision")
        if type(revision) is not int or revision != (charter.revision if charter else 0):
            return Response({"error": "This charter has changed. Reload before saving."}, status=409)
        action = request.data.get("action", "save")
        if not isinstance(action, str) or action not in {"save", "regenerate"}:
            return Response({"error": "Only draft save and vision regeneration are available."}, status=400)
        sources, fingerprint = build_charter_sources(project)
        try:
            vision = sources["draftVision"] if action == "regenerate" else _text(request.data.get("vision"), "Vision", 10000)
            notes = request.data.get("deliverableNotes", {})
            valid_phases = {phase[0] for phase in DELIVERABLES}
            if not isinstance(notes, dict) or set(notes) - valid_phases:
                raise ValueError("Deliverable notes must be keyed by a valid phase.")
            notes = {key: _text(value, "Deliverable note", 2000) for key, value in notes.items()}
            criteria = request.data.get("extraSuccessCriteria", [])
            if not isinstance(criteria, list) or len(criteria) > 50:
                raise ValueError("At most 50 additional success criteria are allowed.")
            criteria = [_text(value, "Success criterion", 1000) for value in criteria]
            if any(not value for value in criteria) or len(set(criteria)) != len(criteria):
                raise ValueError("Success criteria must be non-empty and unique.")
            existing = charter.extra_success_criteria if charter else []
            if criteria[:len(existing)] != existing:
                raise ValueError("Saved success criteria are add-only and cannot be changed or deleted.")
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        if charter is None:
            charter = ProjectCharter(project=project)
        charter.vision = vision
        charter.deliverable_notes = notes
        charter.extra_success_criteria = criteria
        charter.source_fingerprint = fingerprint
        charter.revision += 1
        charter.updated_by = email
        charter.audit_log = [*charter.audit_log, {
            "revision": charter.revision, "action": action,
            "at": timezone.now().isoformat(), "by": email,
        }]
        charter.save()
    return Response(_serialize(project, charter))


@api_view(["GET"])
@require_attributes_access("project_charter")
def list_project_charters(_request):
    rows = [
        {
            "id": charter.id, "projectId": charter.project_id,
            "migrationRequestId": charter.project.migration_request_id,
            "projectName": charter.project.project_name, "requestor": charter.project.requestor,
            "vision": charter.vision, "revision": charter.revision,
            "deliverableNotes": charter.deliverable_notes,
            "extraSuccessCriteria": charter.extra_success_criteria,
            "updatedAt": charter.updated_at.isoformat(), "updatedBy": charter.updated_by,
        }
        for charter in ProjectCharter.objects.select_related("project").order_by("-updated_at")
    ]
    return Response({"rows": rows, "count": len(rows)})


@api_view(["POST"])
@require_attributes_access("project_charter")
def delete_project_charter(request, project_id):
    if not isinstance(request.data, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    with transaction.atomic():
        project = MigrationIntakeSubmission.objects.select_for_update().filter(pk=project_id).first()
        if project is None:
            return Response({"error": "Project not found."}, status=404)
        charter = ProjectCharter.objects.filter(project=project).first()
        if charter is None:
            return Response({"error": "Saved charter not found."}, status=404)
        revision = request.data.get("revision")
        if type(revision) is not int or revision != charter.revision:
            return Response({"error": "This charter has changed. Reload before deleting."}, status=409)
        charter.delete()
    return Response({"deleted": True})
