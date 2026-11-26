from datetime import date
from pathlib import Path
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import (
    MigrationIntakeSubmission,
    PeopleConsultationAuditEntry,
    PeopleConsultationChecklist,
    PeopleConsultationItem,
    StakeholderRegistration,
    UserNameList,
)
from api.permissions.attributes_access import (
    can_access_table,
    get_request_email,
    normalize_email,
)
from api.services.project_artefacts import migration_manager_emails

DEFAULT_ITEMS = [
    ("hr_team_informed", "HR team informed"),
    ("people_impact_assessment", "People impact assessment"),
    ("employee_relations_engaged", "Employee Relations engaged"),
    ("works_council_consultation", "Works council / union consultation"),
    ("local_labour_law_check", "Local labour law check"),
    ("data_privacy", "Data privacy (cross-border work)"),
    ("employee_communication_plan", "Employee communication plan"),
    ("retention_of_key_talent", "Retention of key talent"),
]
EDITABLE_FIELDS = (
    "label",
    "owner_role",
    "owner_user_id",
    "owner_name",
    "owner_email",
    "applicable",
    "na_reason",
    "status",
    "status_date",
    "evidence_url",
    "outcome_note",
)
ALLOWED_STATUSES = {"not_started", "in_progress", "confirmed", "not_applicable"}
MAX_UPLOAD_SIZE = 15 * 1024 * 1024
ALLOWED_EXTENSIONS = {".msg", ".pdf", ".xlsx", ".pptx"}


def _project(project_id):
    try:
        return MigrationIntakeSubmission.objects.get(pk=project_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return None


def _authorize(request, project):
    email = normalize_email(get_request_email(request))
    if not email:
        return "", Response({"error": "Sign in required. Missing SSO email."}, status=401)

    registration = StakeholderRegistration.objects.filter(project=project).first()
    team_emails = {
        normalize_email(person.get("email"))
        for person in (registration.team_members if registration else [])
    }
    if (
        email != normalize_email(project.requestor)
        and email not in team_emails
        and email not in migration_manager_emails(project, registration)
        and not can_access_table(email, "stakeholder_registration")
    ):
        return "", Response(
            {"error": "Only the project requestor, a project team member, or a Stakeholder Registration administrator can access this checklist."},
            status=403,
        )
    return email, None


def _is_migration_manager(project, email, registration=None):
    return email in migration_manager_emails(project, registration)


def _can_manage_owners(project, email, registration=None):
    return (
        _is_migration_manager(project, email, registration)
        or email == normalize_email(project.requestor)
        or can_access_table(email, "stakeholder_registration")
    )


def _get_checklist(project):
    checklist, _created = PeopleConsultationChecklist.objects.get_or_create(project=project)
    existing = set(checklist.items.values_list("item_type", flat=True))
    PeopleConsultationItem.objects.bulk_create([
        PeopleConsultationItem(
            checklist=checklist,
            item_type=item_type,
            label=label,
            sort_order=index,
        )
        for index, (item_type, label) in enumerate(DEFAULT_ITEMS)
        if item_type not in existing
    ])
    return checklist


def _serialize(checklist, viewer_email=""):
    project = checklist.project
    registration = StakeholderRegistration.objects.filter(project=project).first()
    people = [
        {
            "id": str(person.get("id", "")),
            "name": str(person.get("fullName", "")),
            "email": str(person.get("email", "")),
        }
        for person in (registration.team_members if registration else [])
    ]
    items = []
    for item in checklist.items.all():
        items.append({
            "id": item.item_type,
            "pk": item.pk,
            "label": item.label,
            "custom": item.item_type not in dict(DEFAULT_ITEMS),
            "ownerRole": item.owner_role,
            "ownerUserId": item.owner_user_id,
            "ownerName": item.owner_name,
            "ownerEmail": item.owner_email,
            "applicable": item.applicable,
            "naReason": item.na_reason,
            "status": item.status,
            "statusDate": item.status_date.isoformat() if item.status_date else "",
            "evidenceUrl": item.evidence_url,
            "evidenceFileName": Path(item.evidence_file.name).name if item.evidence_file else "",
            "evidenceUrlForDownload": (
                f"/api/migration-dashboard/projects/{project.pk}/people-consultation-compliance/"
                f"evidence/{item.pk}/download/"
                if item.evidence_file else ""
            ),
            "outcomeNote": item.outcome_note,
            "version": item.version,
            "confirmedBy": item.confirmed_by,
            "confirmedAt": item.confirmed_at.isoformat() if item.confirmed_at else "",
            "audit": [
                {
                    "field": entry.field,
                    "old": entry.old_value,
                    "new": entry.new_value,
                    "user": entry.user,
                    "reason": entry.reason,
                    "at": entry.created_at.isoformat(),
                }
                for entry in item.audit_entries.all()
            ],
        })
    return {
        "projectId": project.pk,
        "projectName": project.project_name,
        "migrationRequestId": project.migration_request_id,
        "requestor": project.requestor,
        "phase": "Initiate",
        "canManageOwners": _can_manage_owners(project, viewer_email, registration),
        "isMigrationManager": _is_migration_manager(project, viewer_email, registration),
        "revision": checklist.revision,
        "version": checklist.version,
        "checklistConfirmed": bool(
            checklist.version and checklist.confirmed_revision == checklist.revision
        ),
        "updatedAt": checklist.updated_at.isoformat(),
        "updatedBy": checklist.updated_by,
        "items": items,
        "people": people,
        "auditLog": [
            {
                "item": entry.item.label,
                "field": entry.field,
                "old": entry.old_value,
                "new": entry.new_value,
                "user": entry.user,
                "reason": entry.reason,
                "at": entry.created_at.isoformat(),
            }
            for entry in PeopleConsultationAuditEntry.objects.filter(
                item__checklist=checklist
            ).select_related("item").order_by("-created_at", "-id")[:100]
        ],
    }


def _text(value, label, limit, required=False):
    if not isinstance(value, str) or len(value.strip()) > limit:
        raise ValueError(f"{label} must be text of at most {limit} characters.")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{label} is required.")
    return value


def _normalize_item(raw):
    if not isinstance(raw, dict):
        raise ValueError("Each consideration must be an object.")
    item_type = _text(raw.get("id"), "Item ID", 80, True)
    label = _text(raw.get("label"), "Consideration", 255, True)
    owner_role = _text(raw.get("ownerRole", ""), "Owner role", 128)
    owner_user_id = _text(raw.get("ownerUserId", ""), "Owner ID", 80)
    owner_name = _text(raw.get("ownerName", ""), "Owner name", 255)
    owner_email = _text(raw.get("ownerEmail", ""), "Owner email", 254)
    if owner_email:
        try:
            validate_email(owner_email)
        except ValidationError as exc:
            raise ValueError("Owner email must be a valid email address.") from exc
    applicable = raw.get("applicable")
    if type(applicable) is not bool:
        raise ValueError("Applicability must be Yes or No.")
    status_value = raw.get("status")
    expected_status = status_value if applicable else "not_applicable"
    if expected_status not in ALLOWED_STATUSES or (applicable and status_value == "not_applicable"):
        raise ValueError("Choose a valid status for this consideration.")
    na_reason = _text(raw.get("naReason", ""), "Not applicable reason", 500)
    if not applicable and not na_reason:
        raise ValueError("A reason is required when a consideration is not applicable.")
    status_date = _text(raw.get("statusDate", ""), "Date", 10)
    if status_date:
        try:
            if date.fromisoformat(status_date).isoformat() != status_date:
                raise ValueError
        except ValueError as exc:
            raise ValueError("Date must be a valid YYYY-MM-DD date.") from exc
    evidence_url = _text(raw.get("evidenceUrl", ""), "Evidence link", 1000)
    if evidence_url:
        from django.core.validators import URLValidator
        try:
            URLValidator(schemes=["http", "https"])(evidence_url)
        except ValidationError as exc:
            raise ValueError("Evidence link must be a valid http or https URL.") from exc
    outcome_note = _text(raw.get("outcomeNote", ""), "Outcome note", 500)
    if expected_status == "confirmed" and not status_date:
        raise ValueError("Confirmed items need a date.")
    return {
        "id": item_type,
        "label": label,
        "ownerRole": owner_role,
        "ownerUserId": owner_user_id,
        "ownerName": owner_name,
        "ownerEmail": owner_email,
        "applicable": applicable,
        "naReason": na_reason,
        "status": expected_status,
        "statusDate": status_date,
        "evidenceUrl": evidence_url,
        "outcomeNote": outcome_note,
    }


def _audit(item, field, old_value, new_value, email, reason=""):
    if old_value == new_value:
        return
    PeopleConsultationAuditEntry.objects.create(
        item=item,
        field=field,
        old_value=str(old_value or ""),
        new_value=str(new_value or ""),
        user=email,
        reason=reason,
    )


def _save_items(checklist, raw_items, email, can_manage_owners=True):
    if not isinstance(raw_items, list) or len(raw_items) > 200:
        raise ValueError("Items must be a list of at most 200 considerations.")
    normalized_items = [_normalize_item(raw) for raw in raw_items]
    seen = set()
    prepared = []
    for item_data in normalized_items:
        item_type = item_data["id"]
        if item_type in seen:
            raise ValueError("Consideration IDs must be unique.")
        seen.add(item_type)
        try:
            item = checklist.items.get(item_type=item_type)
        except PeopleConsultationItem.DoesNotExist as exc:
            raise ValueError("A consideration was not found. Reload before saving.") from exc
        values = {
            "label": item_data["label"],
            "owner_role": item_data["ownerRole"],
            "owner_user_id": item_data["ownerUserId"],
            "owner_name": item_data["ownerName"],
            "owner_email": item_data["ownerEmail"],
            "applicable": item_data["applicable"],
            "na_reason": item_data["naReason"],
            "status": item_data["status"],
            "status_date": date.fromisoformat(item_data["statusDate"]) if item_data["statusDate"] else None,
            "evidence_url": item_data["evidenceUrl"],
            "outcome_note": item_data["outcomeNote"],
        }
        owner_fields = {"owner_role", "owner_user_id", "owner_name", "owner_email"}
        if not can_manage_owners and any(
            getattr(item, field) != values[field] for field in owner_fields
        ):
            raise PermissionError(
                "Only the current project's Migration Manager can update consideration owners."
            )
        if item_data["status"] == "confirmed" and not (
            item_data["statusDate"]
            and (
                item_data["evidenceUrl"]
                or item_data["outcomeNote"]
                or bool(item.evidence_file)
            )
        ):
            raise ValueError(
                f'{item_data["label"]} needs a date and evidence or an outcome before it can be confirmed.'
            )
        changed = any(getattr(item, field) != value for field, value in values.items())
        if item.confirmed_at and changed:
            raise ValueError(f"{item.label} is confirmed and frozen. Reopen it with a reason before editing.")
        prepared.append((item, values, changed))
    for item, values, changed in prepared:
        for field, value in values.items():
            old_value = getattr(item, field)
            if old_value != value:
                _audit(item, field, old_value, value, email)
                setattr(item, field, value)
        if changed:
            item.save()
    checklist.revision += 1
    checklist.updated_by = email
    checklist.save(update_fields=["revision", "updated_by", "updated_at"])


@api_view(["GET", "POST"])
def people_consultation_checklist(request, project_id):
    project = _project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=404)
    email, error = _authorize(request, project)
    if error:
        return error

    with transaction.atomic():
        checklist = _get_checklist(project)
        if request.method == "GET":
            return Response(_serialize(checklist, email))
        payload = request.data if isinstance(request.data, dict) else {}
        action = str(payload.get("action") or "save")
        can_manage_owners = _can_manage_owners(
            project,
            email,
            StakeholderRegistration.objects.filter(project=project).first(),
        )
        try:
            expected_revision = payload.get("revision")
            if expected_revision is not None and int(expected_revision) != checklist.revision:
                return Response(
                    {"error": "This checklist changed. Reload before saving."},
                    status=409,
                )
            if action == "save":
                _save_items(checklist, payload.get("items"), email, can_manage_owners)
            elif action == "add_item":
                label = _text(payload.get("label"), "Consideration", 255, True)
                item_type = _text(payload.get("id"), "Item ID", 80, True)
                if checklist.items.filter(item_type=item_type).exists():
                    return Response({"error": "This consideration already exists."}, status=409)
                item = checklist.items.create(
                    item_type=item_type,
                    label=label,
                    sort_order=(checklist.items.order_by("-sort_order").values_list("sort_order", flat=True).first() or 0) + 1,
                )
                checklist.revision += 1
                checklist.updated_by = email
                checklist.save(update_fields=["revision", "updated_by", "updated_at"])
                _audit(item, "created", "", label, email)
            elif action == "confirm":
                normalized_items = [_normalize_item(raw) for raw in payload.get("items", [])]
                for item in normalized_items:
                    if item["status"] == "confirmed" and not (
                        item["statusDate"] and
                        (item["evidenceUrl"] or item["outcomeNote"] or
                         checklist.items.filter(item_type=item["id"], evidence_file__gt="").exists())
                    ):
                        return Response(
                            {"error": f'{item["label"]} needs a date and evidence or an outcome before it can be confirmed.'},
                            status=400,
                        )
                _save_items(checklist, payload.get("items"), email, can_manage_owners)
                now = timezone.now()
                checklist.version += 1
                checklist.revision += 1
                checklist.confirmed_revision = checklist.revision
                checklist.updated_by = email
                checklist.save(update_fields=[
                    "version",
                    "revision",
                    "confirmed_revision",
                    "updated_by",
                    "updated_at",
                ])
                for item in checklist.items.filter(status="confirmed", confirmed_at__isnull=True):
                    item.version = checklist.version
                    item.confirmed_by = email
                    item.confirmed_at = now
                    item.save(update_fields=["version", "confirmed_by", "confirmed_at", "updated_at"])
                    _audit(item, "confirmed", "", checklist.version, email)
            elif action == "reopen":
                item_id = _text(payload.get("id"), "Item ID", 80, True)
                reason = _text(payload.get("reason"), "Reopen reason", 500, True)
                try:
                    item = checklist.items.get(item_type=item_id)
                except PeopleConsultationItem.DoesNotExist:
                    return Response({"error": "Consideration not found."}, status=404)
                if not item.confirmed_at:
                    return Response({"error": "This consideration is not confirmed."}, status=409)
                _audit(item, "reopened", item.version, "", email, reason)
                item.confirmed_at = None
                item.confirmed_by = ""
                item.status = "in_progress"
                item.save(update_fields=["confirmed_at", "confirmed_by", "status", "updated_at"])
                checklist.revision += 1
                checklist.updated_by = email
                checklist.save(update_fields=["revision", "updated_by", "updated_at"])
            else:
                return Response({"error": "Unsupported checklist action."}, status=400)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=403)
        except (TypeError, ValueError) as exc:
            return Response({"error": str(exc)}, status=400)
    return Response(_serialize(checklist, email))


@api_view(["GET"])
def search_consultation_people(request, project_id):
    project = _project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=404)
    email, error = _authorize(request, project)
    if error:
        return error
    registration = StakeholderRegistration.objects.filter(project=project).first()
    if not _can_manage_owners(project, email, registration):
        return Response(
            {"error": "Only the current project's Migration Manager can assign consideration owners."},
            status=403,
        )
    query = str(request.query_params.get("q") or "").strip()
    if len(query) < 2:
        return Response({"error": "Enter at least 2 characters to search."}, status=400)
    matches = UserNameList.objects.filter(
        Q(display_name__icontains=query) | Q(mail__icontains=query)
    ).exclude(mail="").order_by("display_name", "id")[:20]
    return Response({
        "rows": [
            {"id": str(person.pk), "name": person.display_name, "email": person.mail}
            for person in matches
        ]
    })


@api_view(["POST"])
def upload_consultation_evidence(request, project_id, item_id):
    project = _project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=404)
    email, error = _authorize(request, project)
    if error:
        return error
    try:
        item = PeopleConsultationItem.objects.get(
            checklist__project=project, pk=item_id
        )
    except PeopleConsultationItem.DoesNotExist:
        return Response({"error": "Consideration not found."}, status=404)
    if item.confirmed_at:
        return Response({"error": "Reopen this consideration before replacing evidence."}, status=409)
    upload = request.FILES.get("file")
    if not isinstance(upload, UploadedFile):
        return Response({"error": "Choose an evidence file."}, status=400)
    if upload.size > MAX_UPLOAD_SIZE:
        return Response({"error": "Evidence files must be 15 MB or smaller."}, status=400)
    if Path(upload.name).suffix.lower() not in ALLOWED_EXTENSIONS:
        return Response({"error": "Evidence must be an .msg, .pdf, .xlsx, or .pptx file."}, status=400)
    checklist = item.checklist
    expected_revision = request.data.get("revision")
    if expected_revision is not None and str(expected_revision) != str(checklist.revision):
        return Response({"error": "This checklist changed. Reload before uploading evidence."}, status=409)
    old_name = Path(item.evidence_file.name).name if item.evidence_file else ""
    item.evidence_file = upload
    item.save(update_fields=["evidence_file", "updated_at"])
    _audit(item, "evidence_file", old_name, upload.name, email)
    checklist.revision += 1
    checklist.updated_by = email
    checklist.save(update_fields=["revision", "updated_by", "updated_at"])
    return Response(_serialize(item.checklist, email))


@api_view(["GET"])
def download_consultation_evidence(request, project_id, item_id):
    project = _project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=404)
    _email, error = _authorize(request, project)
    if error:
        return error
    try:
        item = PeopleConsultationItem.objects.get(
            checklist__project=project, pk=item_id
        )
    except PeopleConsultationItem.DoesNotExist:
        return Response({"error": "Consideration not found."}, status=404)
    if not item.evidence_file:
        return Response({"error": "No evidence file is attached."}, status=404)
    return FileResponse(
        item.evidence_file.open("rb"),
        as_attachment=True,
        filename=Path(item.evidence_file.name).name,
    )
