from __future__ import annotations

import copy
import re
from uuid import uuid4

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationIntakeSubmission, StakeholderRegistration
from api.permissions.attributes_access import (
    can_access_table,
    get_request_email,
    normalize_email,
    require_attributes_access,
)

STAKEHOLDER_GROUPS = [
    {
        "id": "leadership",
        "label": "Leadership",
        "roles": [
            {"code": "project_sponsor", "label": "Project Sponsor", "required": True, "multiple": False, "description": "Accountable executive sponsor for the migration."},
            {"code": "elt", "label": "ELT", "required": True, "multiple": False, "description": "Executive leadership team member accountable for the function."},
            {"code": "area_functional_leader", "label": "Area Functional Leader", "required": True, "multiple": False, "description": "Functional leader for the sending area."},
            {"code": "gpl", "label": "GPL", "required": True, "multiple": False, "description": "Global process lead for the in-scope activity."},
        ],
    },
    {
        "id": "area",
        "label": "Area",
        "roles": [
            {"code": "area_poc", "label": "Area POC (Migration Owner)", "required": True, "multiple": False, "description": "Area point of contact and migration owner."},
            {"code": "area_sme", "label": "Area SME", "required": True, "multiple": True, "description": "Area subject-matter experts supporting scope and knowledge transfer."},
            {"code": "fpo", "label": "FPO (if applicable)", "required": False, "multiple": False, "description": "Process owner, when applicable."},
        ],
    },
    {
        "id": "gsc",
        "label": "GSC",
        "roles": [
            {"code": "gsc_leaders", "label": "GSC Leaders", "required": True, "multiple": True, "description": "Receiving-site leaders responsible for the transition."},
            {"code": "gsc_head_1", "label": "GSC Head-1", "required": True, "multiple": False, "description": "GSC site head for the receiving location."},
            {"code": "gsc_sme", "label": "GSC SME", "required": True, "multiple": True, "description": "Receiving-site subject-matter experts."},
            {"code": "gsc_fbp", "label": "GSC FBP", "required": True, "multiple": False, "description": "GSC finance business partner."},
            {"code": "gsc_bpm", "label": "GSC BPM", "required": True, "multiple": False, "description": "GSC business process manager."},
        ],
    },
    {
        "id": "project_team",
        "label": "Project Team",
        "roles": [
            {"code": "wpm_focals", "label": "WPM Focals", "required": True, "multiple": True, "description": "WPM focal points assigned to this migration."},
            {"code": "msp_focals", "label": "MSP Focals (if applicable)", "required": False, "multiple": True, "description": "One manually selected project-team focal for each applicable MSP."},
        ],
    },
]
ROLE_DEFINITIONS = {
    role["code"]: role
    for group in STAKEHOLDER_GROUPS
    for role in group["roles"]
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$|^[^@\s]+@localhost$", re.I)


def _empty_assignment(role_code):
    assignment = {
        "lockedAt": "",
        "lockedBy": "",
        "notes": "",
        "notApplicable": False,
    }
    if role_code == "msp_focals":
        assignment["mspRows"] = []
    else:
        assignment["personIds"] = []
    return assignment


def _get_project(project_id):
    try:
        return MigrationIntakeSubmission.objects.get(pk=project_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return None


def _authorize(request, project):
    email = normalize_email(get_request_email(request))
    if not email:
        return None, Response(
            {"error": "Sign in required. Missing SSO email."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if email != normalize_email(project.requestor) and not can_access_table(email, "stakeholder_registration"):
        return None, Response(
            {"error": "Only the project requestor or a user with Stakeholder Registration access can manage this registration."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return email, None


def _serialize(project, registration):
    assignments = copy.deepcopy(registration.assignments or {}) if registration else {}
    for role_code in ROLE_DEFINITIONS:
        assignments.setdefault(role_code, _empty_assignment(role_code))
    return {
        "projectId": project.id,
        "migrationRequestId": project.migration_request_id,
        "projectName": project.project_name,
        "requestor": project.requestor,
        "saved": bool(registration),
        "revision": registration.revision if registration else 0,
        "updatedAt": registration.updated_at.isoformat() if registration else "",
        "updatedBy": registration.updated_by if registration else "",
        "groups": STAKEHOLDER_GROUPS,
        "teamMembers": registration.team_members if registration else [],
        "assignments": assignments,
        "auditLog": registration.audit_log if registration else [],
    }


def _normalize_team_members(raw_members):
    if not isinstance(raw_members, list):
        raise ValueError("Project Team members must be a list.")
    if len(raw_members) > 100:
        raise ValueError("A project can have at most 100 Project Team members.")

    members = []
    seen_emails = set()
    seen_ids = set()
    for index, item in enumerate(raw_members):
        if not isinstance(item, dict):
            raise ValueError(f"Project Team member {index + 1} must be an object.")
        full_name = str(item.get("fullName") or "").strip()
        email = normalize_email(item.get("email"))
        if not full_name:
            raise ValueError(f"Project Team member {index + 1}: name is required.")
        if not email or not EMAIL_RE.match(email):
            raise ValueError(f"Project Team member {index + 1}: enter a valid email.")
        if email in seen_emails:
            raise ValueError(f"{email} is already in the Project Team.")
        member_id = str(item.get("id") or uuid4().hex)
        if member_id in seen_ids:
            raise ValueError("Project Team member IDs must be unique.")
        seen_ids.add(member_id)
        seen_emails.add(email)
        members.append({
            "id": member_id,
            "fullName": full_name[:120],
            "email": email[:254],
            "title": str(item.get("title") or "").strip()[:120],
            "organization": str(item.get("organization") or "").strip()[:120],
            "location": str(item.get("location") or "").strip()[:120],
        })
    return members


def _normalize_person_ids(raw_ids, valid_ids, role):
    if not isinstance(raw_ids, list):
        raise ValueError(f"{role['label']}: assigned people must be a list.")
    person_ids = list(dict.fromkeys(str(value) for value in raw_ids))
    if any(value not in valid_ids for value in person_ids):
        raise ValueError(f"{role['label']}: people must come from this project's Project Team.")
    if not role["multiple"] and len(person_ids) > 1:
        raise ValueError(f"{role['label']} accepts one person.")
    return person_ids


def _normalize_assignments(raw_assignments, team_members):
    if not isinstance(raw_assignments, dict):
        raise ValueError("Role assignments must be an object.")
    valid_ids = {person["id"] for person in team_members}
    assignments = {}
    for role_code, role in ROLE_DEFINITIONS.items():
        raw = raw_assignments.get(role_code, {})
        if not isinstance(raw, dict):
            raise ValueError(f"{role['label']}: assignment must be an object.")
        assignment = _empty_assignment(role_code)
        assignment["notes"] = str(raw.get("notes") or "").strip()[:1000]
        assignment["notApplicable"] = raw.get("notApplicable") is True
        if assignment["notApplicable"] and role["required"]:
            raise ValueError(f"{role['label']} is required and cannot be marked not applicable.")

        if role_code == "msp_focals":
            rows = raw.get("mspRows", [])
            if not isinstance(rows, list):
                raise ValueError("MSP Focals must be a list of MSP assignments.")
            seen_msps = set()
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    raise ValueError(f"MSP row {index + 1} must be an object.")
                msp_name = str(row.get("mspName") or "").strip()
                if not msp_name:
                    raise ValueError(f"MSP row {index + 1}: MSP name is required.")
                if msp_name.casefold() in seen_msps:
                    raise ValueError(f"MSP '{msp_name}' is listed more than once.")
                seen_msps.add(msp_name.casefold())
                person_ids = _normalize_person_ids(row.get("personIds", []), valid_ids, role)
                if len(person_ids) > 1:
                    raise ValueError(f"{msp_name} accepts one focal person.")
                assignment["mspRows"].append({"mspName": msp_name[:120], "personIds": person_ids})
        else:
            assignment["personIds"] = _normalize_person_ids(raw.get("personIds", []), valid_ids, role)
        assignment["lockedAt"] = str(raw.get("lockedAt") or "")
        assignment["lockedBy"] = str(raw.get("lockedBy") or "")
        assignments[role_code] = assignment
    return assignments


def _assignment_content(assignment):
    return {
        key: assignment.get(key)
        for key in ("personIds", "mspRows", "notApplicable", "notes")
        if key in assignment
    }


def _role_is_filled(role, assignment):
    if assignment.get("notApplicable"):
        return True
    if role["code"] == "msp_focals":
        rows = assignment.get("mspRows", [])
        return bool(rows) and all(len(row.get("personIds", [])) == 1 for row in rows)
    return bool(assignment.get("personIds"))


def _append_audit(registration, email, action, role_code="", details=""):
    registration.audit_log.append({
        "action": action,
        "roleCode": role_code,
        "details": details,
        "by": email,
        "at": timezone.now().isoformat(),
    })
    registration.updated_by = email
    registration.revision += 1
    registration.save(update_fields=["audit_log", "updated_by", "revision", "updated_at"])


@api_view(["GET"])
def get_stakeholder_registration(request, project_id):
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    email, error = _authorize(request, project)
    if error:
        return error
    registration = StakeholderRegistration.objects.filter(project=project).first()
    return Response(_serialize(project, registration))


@api_view(["POST"])
def save_stakeholder_registration(request, project_id):
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    email, error = _authorize(request, project)
    if error:
        return error
    payload = request.data if isinstance(request.data, dict) else {}
    action = str(payload.get("action") or "save").strip().lower()
    if action not in {"save", "lock", "unlock", "lock_all"}:
        return Response({"error": "Unsupported action."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        registration = StakeholderRegistration.objects.select_for_update().filter(project=project).first()
        if action == "save":
            try:
                team_members = _normalize_team_members(
                    payload.get("teamMembers", registration.team_members if registration else [])
                )
                new_assignments = _normalize_assignments(
                    payload.get("assignments", registration.assignments if registration else {}),
                    team_members,
                )
            except ValueError as exc:
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

            previous_assignments = registration.assignments if registration else {}
            for role_code, next_assignment in new_assignments.items():
                previous = previous_assignments.get(role_code, _empty_assignment(role_code))
                if previous.get("lockedAt") and _assignment_content(previous) != _assignment_content(next_assignment):
                    return Response(
                        {"error": f"{ROLE_DEFINITIONS[role_code]['label']} is locked. Unlock it before editing."},
                        status=status.HTTP_409_CONFLICT,
                    )
                next_assignment["lockedAt"] = previous.get("lockedAt", "")
                next_assignment["lockedBy"] = previous.get("lockedBy", "")

            if registration is None:
                registration = StakeholderRegistration.objects.create(
                    project=project,
                    team_members=team_members,
                    assignments=new_assignments,
                )
            else:
                registration.team_members = team_members
                registration.assignments = new_assignments
            _append_audit(registration, email, "save", details="Saved Project Team and stakeholder assignments.")
        else:
            if registration is None or not registration.assignments:
                return Response(
                    {"error": "Save the Project Team and assignments before locking."},
                    status=status.HTTP_409_CONFLICT,
                )
            assignments = copy.deepcopy(registration.assignments)
            if action == "lock_all":
                missing = [
                    role["label"] for role in ROLE_DEFINITIONS.values()
                    if role["required"] and not _role_is_filled(role, assignments.get(role["code"], {}))
                ]
                if missing:
                    return Response(
                        {"error": f"Assign required roles before locking: {', '.join(missing)}."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                role_codes = [
                    code for code, assignment in assignments.items()
                    if _role_is_filled(ROLE_DEFINITIONS[code], assignment)
                ]
            else:
                role_code = str(payload.get("roleCode") or "")
                if role_code not in ROLE_DEFINITIONS:
                    return Response({"error": "Choose a valid role."}, status=status.HTTP_400_BAD_REQUEST)
                role_codes = [role_code]

            for role_code in role_codes:
                role = ROLE_DEFINITIONS[role_code]
                assignment = assignments.setdefault(role_code, _empty_assignment(role_code))
                if action in {"lock", "lock_all"}:
                    if not _role_is_filled(role, assignment):
                        return Response({"error": f"Assign {role['label']} before locking."}, status=status.HTTP_400_BAD_REQUEST)
                    if not assignment.get("lockedAt"):
                        assignment["lockedAt"] = timezone.now().isoformat()
                        assignment["lockedBy"] = email
                else:
                    assignment["lockedAt"] = ""
                    assignment["lockedBy"] = ""
            registration.assignments = assignments
            registration.save(update_fields=["assignments", "updated_at"])
            _append_audit(
                registration,
                email,
                action,
                role_code="*" if action == "lock_all" else role_codes[0],
                details=f"{action.replace('_', ' ').title()} stakeholder assignment.",
            )

    return Response(_serialize(project, registration))


@api_view(["GET"])
@require_attributes_access("stakeholder_registration")
def list_stakeholder_registrations(_request):
    registrations = (
        StakeholderRegistration.objects.select_related("project")
        .order_by("project__migration_request_id")
    )
    columns = [
        {"key": "migration_request_id", "label": "Migration Request ID"},
        {"key": "project_name", "label": "Project Name"},
        {"key": "requestor", "label": "Requestor"},
        {"key": "team_members", "label": "Project Team"},
        {"key": "roles_filled", "label": "Roles Filled"},
        {"key": "roles_locked", "label": "Roles Locked"},
        {"key": "revision", "label": "Revision"},
        {"key": "updated_by", "label": "Last Updated By"},
        {"key": "updated_at", "label": "Last Updated"},
    ]
    columns.extend(
        {"key": role_code, "label": ROLE_DEFINITIONS[role_code]["label"]}
        for role_code in ROLE_DEFINITIONS
    )

    rows = []
    for registration in registrations:
        members = registration.team_members or []
        by_id = {person["id"]: person for person in members}
        assignments = registration.assignments or {}
        filled_count = 0
        locked_count = 0
        row = {
            "registration_id": registration.id,
            "project_id": registration.project_id,
            "migration_request_id": registration.project.migration_request_id,
            "project_name": registration.project.project_name,
            "requestor": registration.project.requestor,
            "team_members": "; ".join(
                f"{person.get('fullName', '')} <{person.get('email', '')}>" for person in members
            ),
            "revision": registration.revision,
            "updated_by": registration.updated_by,
            "updated_at": registration.updated_at.isoformat(),
            "audit_log": registration.audit_log or [],
        }
        for role_code, role in ROLE_DEFINITIONS.items():
            assignment = assignments.get(role_code, _empty_assignment(role_code))
            is_filled = _role_is_filled(role, assignment)
            if role["required"] and is_filled:
                filled_count += 1
            if role["required"] and is_filled and assignment.get("lockedAt"):
                locked_count += 1
            if role_code == "msp_focals":
                value = "; ".join(
                    f"{item['mspName']}: {', '.join(by_id[person_id]['fullName'] for person_id in item['personIds'] if person_id in by_id) or 'To assign'}"
                    for item in assignment.get("mspRows", [])
                )
            elif assignment.get("notApplicable"):
                value = "Not applicable"
            else:
                value = ", ".join(
                    by_id[person_id]["fullName"]
                    for person_id in assignment.get("personIds", [])
                    if person_id in by_id
                )
            row[role_code] = value
        row["roles_filled"] = f"{filled_count} / {sum(role['required'] for role in ROLE_DEFINITIONS.values())}"
        row["roles_locked"] = f"{locked_count} / {sum(role['required'] for role in ROLE_DEFINITIONS.values())}"
        rows.append(row)
    return Response({"count": len(rows), "columns": columns, "rows": rows})