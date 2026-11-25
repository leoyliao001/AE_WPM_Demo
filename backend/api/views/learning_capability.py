import json
import os
import re

from django.core.files.storage import default_storage
from django.db import transaction
from django.http import FileResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import LearningCapabilityRecord, MigrationIntakeSubmission, MigrationTeam, StakeholderRegistration
from api.permissions.attributes_access import build_access_snapshot, get_request_email, normalize_email
from api.services.learning_capability import validate_learning_state
from api.services.project_artefacts import project_permissions


MAX_EVIDENCE_SIZE = 5 * 1024 * 1024
ALLOWED_EVIDENCE_EXTENSIONS = {".xlsx", ".xls", ".csv", ".pdf", ".msg", ".eml", ".docx"}


def _record_permissions(project, email):
    is_super_admin = bool(build_access_snapshot(email).get("is_super_admin"))
    registration = StakeholderRegistration.objects.filter(project=project).first()
    assignment = (registration.assignments or {}).get("migration_manager") if registration else None
    raw_assigned_ids = assignment.get("personIds", []) if isinstance(assignment, dict) else []
    assigned_ids = {str(value) for value in raw_assigned_ids} if isinstance(raw_assigned_ids, list) else set()
    assigned_manager_emails = {
        normalize_email(manager.email)
        for manager in MigrationTeam.objects.filter(role="Manager")
        if f"migration-team-{manager.pk}" in assigned_ids
    }
    can_edit = is_super_admin or email in assigned_manager_emails
    can_view = can_edit or project_permissions(project, email, "resources")["view"]
    return {"view": can_view, "edit": can_edit}


def _evidence_data(project, record):
    if not record or not record.evidence:
        return None
    return {
        "name": record.evidence_name,
        "size": record.evidence_size,
        "type": record.evidence_type,
        "url": f"/api/migration-dashboard/projects/{project.pk}/learning-capability/evidence/",
    }


def _response_data(project, record, permissions):
    return {
        "projectId": project.pk,
        "state": record.state if record else {},
        "saved": record is not None,
        "revision": record.revision if record else 0,
        "updatedAt": record.updated_at.isoformat() if record else "",
        "updatedBy": record.updated_by if record else "",
        "evidence": _evidence_data(project, record),
        "permissions": permissions,
    }


def _parse_revision(value):
    if value is None or isinstance(value, bool) or not re.fullmatch(r"\d+", str(value)):
        raise ValueError("A valid learning record revision is required.")
    return int(value)


@api_view(["GET", "PUT"])
def learning_capability(request, project_id):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=401)

    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if not project:
        return Response({"error": "Project not found."}, status=404)
    permissions = _record_permissions(project, email)
    if not permissions["view"]:
        return Response({"error": "Only the project requestor, Project Team or users with project access can view L&D data."}, status=403)

    if request.method == "GET":
        record = LearningCapabilityRecord.objects.filter(project=project).first()
        return Response(_response_data(project, record, permissions))

    if not permissions["edit"]:
        return Response({"error": "Only the assigned Project Migration Manager or a Platform Super Admin can save L&D data."}, status=403)

    payload = request.data
    raw_state = payload.get("state") if hasattr(payload, "get") else None
    if isinstance(raw_state, str):
        try:
            raw_state = json.loads(raw_state)
        except json.JSONDecodeError:
            return Response({"error": "Learning state must contain valid JSON."}, status=400)
    try:
        state = validate_learning_state(raw_state)
        revision = _parse_revision(payload.get("revision"))
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)

    upload = request.FILES.get("evidence")
    remove_evidence = str(payload.get("removeEvidence", "")).lower() in {"true", "1"}
    if upload and remove_evidence:
        return Response({"error": "Choose either a new evidence file or remove the current file."}, status=400)
    if upload:
        extension = os.path.splitext(upload.name)[1].lower()
        if extension not in ALLOWED_EVIDENCE_EXTENSIONS:
            return Response({"error": "Evidence must be an Excel, CSV, PDF, MSG, EML or DOCX file."}, status=400)
        if upload.size > MAX_EVIDENCE_SIZE:
            return Response({"error": "Evidence files must be 5 MB or smaller."}, status=400)
        file_name = os.path.basename(upload.name.replace("\\", "/")).strip()
        if not file_name or len(file_name) > 255:
            return Response({"error": "Evidence file name must be 255 characters or fewer."}, status=400)

    old_file_name = ""
    with transaction.atomic():
        project = MigrationIntakeSubmission.objects.select_for_update().filter(pk=project_id).first()
        if not project:
            return Response({"error": "Project not found."}, status=404)
        permissions = _record_permissions(project, email)
        if not permissions["edit"]:
            return Response({"error": "Only the assigned Project Migration Manager or a Platform Super Admin can save L&D data."}, status=403)
        record = LearningCapabilityRecord.objects.select_for_update().filter(project=project).first()
        current_revision = record.revision if record else 0
        if revision != current_revision:
            return Response({"error": "L&D data changed since it was loaded. Reload before saving; your inputs have been retained."}, status=409)

        if record is None:
            record = LearningCapabilityRecord(project=project)
        old_file_name = record.evidence.name if record.evidence else ""
        record.state = state
        record.revision += 1
        record.updated_by = email
        if upload:
            record.evidence.save(file_name, upload, save=False)
            record.evidence_name = file_name
            record.evidence_size = upload.size
            record.evidence_type = (upload.content_type or "application/octet-stream")[:128]
        elif remove_evidence:
            record.evidence = None
            record.evidence_name = ""
            record.evidence_size = None
            record.evidence_type = ""
        record.save()
        if old_file_name and old_file_name != (record.evidence.name if record.evidence else ""):
            transaction.on_commit(lambda name=old_file_name: default_storage.delete(name))

    return Response(_response_data(project, record, permissions))


@api_view(["GET"])
def download_learning_evidence(request, project_id):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=401)
    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if not project:
        return Response({"error": "Project not found."}, status=404)
    if not _record_permissions(project, email)["view"]:
        return Response({"error": "You do not have permission to view this evidence."}, status=403)
    record = LearningCapabilityRecord.objects.filter(project=project).first()
    if not record or not record.evidence:
        return Response({"error": "Evidence file not found."}, status=404)
    return FileResponse(
        record.evidence.open("rb"),
        as_attachment=True,
        filename=record.evidence_name or os.path.basename(record.evidence.name),
        content_type="application/octet-stream",
    )
