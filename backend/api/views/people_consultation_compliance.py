from copy import deepcopy
from datetime import date
import mimetypes
import os

from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import (
    MigrationIntakeSubmission, PeopleConsultationCompliance, PeopleConsultationEvidence,
)
from api.permissions.attributes_access import get_request_email, normalize_email
from api.services.project_artefacts import project_permissions, text


DEFAULT_ITEMS = [
    ("hr-team-informed", "HR team informed"),
    ("people-impact-assessment", "People impact assessment"),
    ("employee-relations-engaged", "Employee Relations engaged"),
    ("works-council-consultation", "Works council / union consultation"),
    ("local-labour-law-check", "Local labour law check"),
    ("data-privacy-cross-border", "Data privacy (cross-border work)"),
    ("employee-communication-plan", "Employee communication plan"),
    ("retention-of-key-talent", "Retention of key talent"),
]
STATUSES = {"not_started", "in_progress", "confirmed", "not_applicable"}
ITEM_FIELDS = (
    "consideration", "ownerRole", "ownerName", "applicable", "reason",
    "status", "statusDate", "evidence", "outcomeNote",
)


def _blank_items():
    return [
        {
            "id": item_id, "consideration": label, "ownerRole": "", "ownerName": "",
            "applicable": True, "reason": "", "status": "not_started",
            "statusDate": "", "evidence": "", "outcomeNote": "", "custom": False,
        }
        for item_id, label in DEFAULT_ITEMS
    ]


def _serialize(project, record, permissions):
    items = deepcopy(record.items) if record else _blank_items()
    files_by_item = {}
    for evidence in PeopleConsultationEvidence.objects.filter(project=project):
        files_by_item.setdefault(evidence.item_id, []).append({
            "id": evidence.pk,
            "name": evidence.original_name,
            "size": evidence.size,
            "url": f"/api/migration-dashboard/projects/{project.pk}/people-consultation-compliance/evidence/{evidence.pk}/",
        })
    for item in items:
        item["evidenceFiles"] = files_by_item.get(item["id"], [])
    return {
        "projectId": project.pk,
        "projectName": project.project_name,
        "migrationRequestId": project.migration_request_id,
        "phase": project.status,
        "items": items,
        "status": record.status if record else "draft",
        "version": record.version if record else 0,
        "revision": record.revision if record else 0,
        "saved": record is not None,
        "updatedAt": record.updated_at.isoformat() if record else "",
        "updatedBy": record.updated_by if record else "",
        "auditLog": deepcopy(record.audit_log) if record else [],
        "permissions": permissions,
    }


def _normalize_items(raw_items, evidence_item_ids=None):
    evidence_item_ids = evidence_item_ids or set()
    if not isinstance(raw_items, list) or not 8 <= len(raw_items) <= 100:
        raise ValueError("The checklist must include all 8 standard items and no more than 92 added considerations.")
    normalized = []
    seen = set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise ValueError("Each consideration must be an object.")
        item_id = text(raw.get("id"), "Item ID", 80, True)
        if item_id in seen:
            raise ValueError("Consideration IDs must be unique.")
        seen.add(item_id)
        is_custom = item_id not in {key for key, _ in DEFAULT_ITEMS}
        consideration = text(raw.get("consideration"), "Consideration", 200, True)
        if not is_custom and consideration != dict(DEFAULT_ITEMS)[item_id]:
            raise ValueError("Standard checklist considerations cannot be renamed.")
        applicable = raw.get("applicable")
        if type(applicable) is not bool:
            raise ValueError("Choose Yes or No for every consideration.")
        reason = text(raw.get("reason", ""), "Reason", 1000)
        status = raw.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError("Choose a valid checklist status.")
        if not applicable:
            if not reason.strip():
                raise ValueError("A reason is required when a consideration is not applicable.")
            status = "not_applicable"
        elif status == "not_applicable":
            raise ValueError("Applicable considerations cannot be marked Not applicable.")
        status_date = text(raw.get("statusDate", ""), "Date", 10)
        if status_date:
            try:
                date.fromisoformat(status_date)
            except ValueError as exc:
                raise ValueError("Enter a valid checklist date.") from exc
        evidence = text(raw.get("evidence", ""), "Evidence", 2000)
        outcome_note = text(raw.get("outcomeNote", ""), "Outcome note", 500)
        if status == "confirmed" and (
            not status_date or not (evidence or outcome_note or item_id in evidence_item_ids)
        ):
            raise ValueError("Confirmed items need a date and evidence or an outcome note.")
        normalized.append({
            "id": item_id,
            "consideration": consideration,
            "ownerRole": text(raw.get("ownerRole", ""), "Owner role", 120),
            "ownerName": text(raw.get("ownerName", ""), "Owner name", 200),
            "applicable": applicable,
            "reason": reason,
            "status": status,
            "statusDate": status_date,
            "evidence": evidence,
            "outcomeNote": outcome_note,
            "custom": is_custom,
        })
    for item_id, _ in DEFAULT_ITEMS:
        if item_id not in seen:
            raise ValueError("All 8 standard checklist items must remain on the checklist.")
    return normalized


@api_view(["GET", "POST"])
def people_consultation_compliance(request, project_id):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required."}, status=401)
    with transaction.atomic():
        projects = MigrationIntakeSubmission.objects.select_for_update() if request.method == "POST" else MigrationIntakeSubmission.objects
        project = projects.filter(pk=project_id).first()
        if not project:
            return Response({"error": "Project not found."}, status=404)
        permissions = project_permissions(project, email, "business_impact_analysis")
        if not permissions["view"]:
            return Response({"error": "Only project members can view this checklist."}, status=403)
        record = PeopleConsultationCompliance.objects.filter(project=project).first()
        if request.method == "GET":
            return Response(_serialize(project, record, permissions))
        if not permissions["edit"]:
            return Response({"error": "Only the project requestor, WPM focal or an authorised administrator can edit this checklist."}, status=403)
        payload = request.data
        if not isinstance(payload, dict):
            return Response({"error": "Request body must be an object."}, status=400)
        expected_revision = record.revision if record else 0
        if type(payload.get("revision")) is not int or payload["revision"] != expected_revision:
            return Response({"error": "This checklist changed. Reload before saving; your inputs have been retained."}, status=409)
        action = payload.get("action", "save")
        if not isinstance(action, str) or action not in {"save", "confirm", "reopen"}:
            return Response({"error": "Unsupported checklist action."}, status=400)
        if record and record.status == "confirmed" and action != "reopen":
            return Response({"error": "The confirmed checklist is frozen. Reopen it with a reason before editing."}, status=409)
        old_items = deepcopy(record.items) if record else _blank_items()
        reason = ""
        try:
            if action == "reopen":
                if not record or record.status != "confirmed":
                    raise ValueError("Only a confirmed checklist can be reopened.")
                reason = text(payload.get("reason"), "Reopen reason", 2000, True)
                items = deepcopy(record.items)
                record.status = "draft"
                record.version += 1
            else:
                evidence_item_ids = set(
                    PeopleConsultationEvidence.objects.filter(project=project).values_list("item_id", flat=True)
                )
                items = _normalize_items(payload.get("items"), evidence_item_ids)
                if record is None:
                    record = PeopleConsultationCompliance(project=project)
                if action == "confirm":
                    record.version += 1
                    record.status = "confirmed"
                else:
                    record.status = "draft"
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        if record is None:
            record = PeopleConsultationCompliance(project=project)
        record.items = items
        record.revision += 1
        record.updated_by = email
        now = timezone.now().isoformat()
        old_by_id = {item["id"]: item for item in old_items}
        new_by_id = {item["id"]: item for item in items}
        changes = []
        if action == "reopen":
            changes.append({
                "item": "", "field": "status", "old": "confirmed", "new": "draft",
                "user": email, "at": now, "reason": reason, "version": record.version,
            })
        else:
            for item in items:
                previous = old_by_id.get(item["id"], {})
                for field in ITEM_FIELDS:
                    if previous.get(field) != item.get(field):
                        changes.append({
                            "item": item["id"], "field": field, "old": previous.get(field),
                            "new": item.get(field), "user": email, "at": now, "reason": "",
                            "version": record.version,
                        })
            if action == "confirm":
                changes.append({
                    "item": "", "field": "status", "old": "draft", "new": "confirmed",
                    "user": email, "at": now, "reason": "", "version": record.version,
                })
        record.audit_log = [*record.audit_log, *changes]
        record.save()
        return Response(_serialize(project, record, permissions))


@api_view(["POST", "DELETE"])
def people_consultation_evidence(request, project_id):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required."}, status=401)
    with transaction.atomic():
        project = MigrationIntakeSubmission.objects.select_for_update().filter(pk=project_id).first()
        if not project:
            return Response({"error": "Project not found."}, status=404)
        permissions = project_permissions(project, email, "business_impact_analysis")
        if not permissions["view"]:
            return Response({"error": "Only project members can access this checklist."}, status=403)
        if not permissions["edit"]:
            return Response({"error": "Only the project requestor, WPM focal or an authorised administrator can change evidence."}, status=403)
        record = PeopleConsultationCompliance.objects.filter(project=project).first()
        if not record:
            return Response({"error": "Save the checklist before adding evidence."}, status=409)
        if record.status == "confirmed":
            return Response({"error": "The confirmed checklist is frozen. Reopen it before changing evidence."}, status=409)
        revision = request.data.get("revision")
        if isinstance(revision, str):
            try:
                revision = int(revision)
            except ValueError:
                revision = None
        if type(revision) is not int or revision != record.revision:
            return Response({"error": "This checklist changed. Reload before changing evidence."}, status=409)
        if request.method == "POST":
            item_id = request.data.get("itemId", "")
            upload = request.FILES.get("file")
            if not isinstance(item_id, str) or item_id not in {item["id"] for item in record.items}:
                return Response({"error": "Choose a checklist item for this evidence."}, status=400)
            if upload is None:
                return Response({"error": "Choose a file to upload."}, status=400)
            extension = os.path.splitext(upload.name)[1].lower()
            if extension not in {".msg", ".pdf", ".xlsx", ".pptx"}:
                return Response({"error": "Only MSG, PDF, XLSX and PPTX evidence files are accepted."}, status=400)
            if upload.size > 20 * 1024 * 1024:
                return Response({"error": "Evidence files must be 20 MB or smaller."}, status=400)
            name = os.path.basename(upload.name.replace("\\", "/"))
            if not name or len(name) > 255:
                return Response({"error": "The evidence file name must be 1–255 characters."}, status=400)
            evidence = PeopleConsultationEvidence.objects.create(
                project=project, item_id=item_id, file=upload,
                original_name=name, size=upload.size, uploaded_by=email,
            )
            action = "upload"
            previous = []
            new = [{"id": evidence.pk, "name": evidence.original_name}]
        else:
            evidence_id = request.data.get("evidenceId")
            if type(evidence_id) is not int:
                return Response({"error": "Choose an evidence file to remove."}, status=400)
            evidence = PeopleConsultationEvidence.objects.filter(project=project, pk=evidence_id).first()
            if not evidence:
                return Response({"error": "Evidence file not found."}, status=404)
            action = "delete"
            previous = [{"id": evidence.pk, "name": evidence.original_name}]
            new = []
            evidence.file.delete(save=False)
            evidence.delete()
        record.revision += 1
        record.updated_by = email
        record.audit_log = [*record.audit_log, {
            "item": evidence.item_id, "field": "evidenceFiles",
            "old": previous, "new": new, "user": email,
            "at": timezone.now().isoformat(), "reason": "", "version": record.version,
        }]
        record.save()
        return Response(_serialize(project, record, permissions))


@api_view(["GET"])
def download_people_consultation_evidence(request, project_id, evidence_id):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required."}, status=401)
    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if not project:
        return Response({"error": "Project not found."}, status=404)
    permissions = project_permissions(project, email, "business_impact_analysis")
    if not permissions["view"]:
        return Response({"error": "Only project members can access this checklist."}, status=403)
    evidence = PeopleConsultationEvidence.objects.filter(project=project, pk=evidence_id).first()
    if not evidence:
        return Response({"error": "Evidence file not found."}, status=404)
    content_type = mimetypes.guess_type(evidence.original_name)[0] or "application/octet-stream"
    return FileResponse(
        evidence.file.open("rb"),
        as_attachment=True,
        filename=evidence.original_name,
        content_type=content_type,
    )
