from copy import deepcopy

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import AccessEnablement, ApprovalWorkflow, BusinessCase, MigrationIntakeSubmission, ProjectResources, StakeholderRegistration
from api.permissions.attributes_access import build_access_snapshot, get_request_email, normalize_email
from api.services.business_case import online_case_is_approved
from api.services.project_artefacts import (
    AREA_FIELDS, BARRIER_TYPES, EXECUTION_FIELDS, HIRING_STATUSES, HIRING_TYPES,
    HR_FIELDS, IT_ITEMS, LANGUAGES, SYSTEM_CATALOGUE, access_summary, date_value,
    integer, project_permissions, resource_ready, resource_sites, rows_list, scope_source, text,
)


def _serialize(project, record, kind, email):
    source = scope_source(project)
    permissions = project_permissions(project, email, kind)
    changed = bool(record and record.source_version != source["version"])
    result = {
        "projectId": project.pk, "projectName": project.project_name,
        "migrationRequestId": project.migration_request_id, "requestor": project.requestor,
        "region": project.region, "areas": project.areas, "countries": project.countries,
        "products": project.products,
        "sites": (project.default_location_strategies or []) + (project.custom_location_strategies or []),
        "source": source, "sourceChanged": changed, "permissions": permissions,
        "saved": record is not None, "revision": record.revision if record else 0,
        "updatedAt": record.updated_at.isoformat() if record else "",
        "updatedBy": record.updated_by if record else "", "auditLog": record.audit_log if record else [],
        "frozen": bool(record and record.status == "confirmed"),
    }
    if kind == "resources":
        rows = record.rows if record else []
        ready = resource_ready(rows, source)
        result.update({
            "rows": rows, "ready": ready, "hiringTypes": HIRING_TYPES,
            "hiringStatuses": HIRING_STATUSES, "languages": LANGUAGES,
            "siteOptions": resource_sites(project),
            "status": "needs_review" if changed and result["frozen"] else "confirmed" if result["frozen"] else "ready" if ready else "draft",
        })
    else:
        systems = record.systems if record else []
        barriers = record.barriers if record else []
        items = record.it_items if record and record.it_items else [{"id": item["id"], "qtyConfirmed": 0} for item in IT_ITEMS]
        confirmation = record.it_confirmation if record else {}
        summary = access_summary(systems, barriers, items, confirmation, source)
        result.update({
            "systems": systems, "barriers": barriers, "itItems": items,
            "itConfirmation": confirmation, "summary": summary,
            "savedBarrierIds": [barrier["id"] for barrier in barriers],
            "catalogue": SYSTEM_CATALOGUE, "standardItems": IT_ITEMS, "barrierTypes": BARRIER_TYPES,
            "status": "needs_review" if changed and result["frozen"] else "confirmed" if result["frozen"] else
                      "ready" if summary["ready"] else "at_risk" if record and not summary["ready"] else "draft",
        })
        registration = StakeholderRegistration.objects.filter(project=project).first()
        people = {person["id"]: person["email"] for person in registration.team_members} if registration else {}
        result["itContacts"] = sorted({
            people[person_id] for code, assignment in (registration.assignments if registration else {}).items()
            if code in {"gsc_leaders", "gsc_head_1"} and assignment.get("lockedAt")
            for person_id in assignment.get("personIds", []) if person_id in people
        })
    return result


def _resource_rows(payload, record, permissions, action, email):
    raw = rows_list(payload.get("rows", record.rows if record else []), "Resources")
    previous = {row["id"]: row for row in (record.rows if record else [])}
    if not permissions["edit"] and set(previous) != {row["id"] for row in raw}:
        raise PermissionError("Only a project lead or Resources administrator can add or remove resources.")
    if any(row.get("areaLockedAt") and row["id"] not in {item["id"] for item in raw} for row in previous.values()):
        raise ValueError("Reopen Area details before removing a submitted resource.")
    result = []
    for row in raw:
        old = previous.get(row["id"], {})
        normalized = {"id": row["id"]}
        for field in EXECUTION_FIELDS + AREA_FIELDS + HR_FIELDS:
            value = row.get(field, "")
            normalized[field] = date_value(value, field) if field.endswith("Date") or field.endswith("Doj") else text(value, field)
        if normalized["hiringType"] not in HIRING_TYPES:
            raise ValueError("Choose External, IJP or Efficiency for each resource.")
        if normalized["language"] and normalized["language"] not in LANGUAGES:
            raise ValueError("Choose a language from the catalogue.")
        if normalized["hiringStatus"] not in HIRING_STATUSES + ["Not Applicable"]:
            raise ValueError("Choose a valid hiring status.")
        if not permissions["edit"] and any(normalized[field] != old.get(field, "") for field in EXECUTION_FIELDS + HR_FIELDS):
            raise PermissionError("Execution and HR / TAA details require project lead or Resources access.")
        if not permissions["area"] and any(normalized[field] != old.get(field, "") for field in AREA_FIELDS):
            raise PermissionError("Area details require a locked Area POC assignment or Resources access.")
        if old.get("areaLockedAt") and any(normalized[field] != old[field] for field in AREA_FIELDS):
            raise ValueError("Reopen Area details before changing submitted Area fields.")
        for key in ("areaLockedAt", "areaLockedBy"):
            normalized[key] = old.get(key, "")
        if normalized["hiringType"] == "Efficiency":
            normalized.update({"hiringStatus": "Not Applicable", "requisitionId": "", "tentativeDoj": ""})
        elif normalized["hiringStatus"] == "Not Applicable":
            raise ValueError("Not Applicable is reserved for Efficiency resources.")
        if normalized["actualDoj"] and normalized["pidCreationDate"] and normalized["actualDoj"] < normalized["pidCreationDate"]:
            raise ValueError("Actual DOJ cannot be earlier than PID creation.")
        if normalized["hiringStatus"] == "Onboarded" and not all(normalized[field] for field in ("actualDoj", "apmmId", "requisitionId")):
            raise ValueError("Onboarded resources require Actual DOJ, APMM ID and Requisition ID.")
        if action == "submit_area":
            if not normalized["areaPid"]:
                raise ValueError("Area PID is required for every row before submitting Area details.")
            if not normalized["areaLockedAt"]:
                normalized.update({"areaLockedAt": timezone.now().isoformat(), "areaLockedBy": email})
        if action == "reopen_area":
            normalized.update({"areaLockedAt": "", "areaLockedBy": ""})
        result.append(normalized)
    if action == "submit_area" and not result:
        raise ValueError("Add at least one resource before submitting Area details.")
    return result


def _access_data(payload, record, permissions, source, email):
    systems = []
    raw = rows_list(payload.get("systems", record.systems if record else []), "Systems", 100)
    for row in raw:
        system = text(row.get("systemId"), "System", required=True)
        if system not in {item["id"] for item in SYSTEM_CATALOGUE}:
            raise ValueError("Choose a system from the catalogue.")
        if type(row.get("isSecured")) is not bool:
            raise ValueError("Each system must have a Yes / No secured status.")
        systems.append({
            "id": row["id"], "systemId": system,
            "accessType": text(row.get("accessType", ""), "Access / licence type"),
            "usersNeeded": integer(row.get("usersNeeded"), "Users needed"),
            "isSecured": row["isSecured"],
        })
    if len({row["systemId"] for row in systems}) != len(systems):
        raise ValueError("Each catalogue system can only be recorded once.")
    old_systems = record.systems if record else []
    if not permissions["edit"] and systems != old_systems:
        raise PermissionError("Only the project lead or Access & Enablement administrator can change systems.")
    raw_barriers = rows_list(payload.get("barriers", []), "Barriers", 500)
    old_barriers = {row["id"]: row for row in (record.barriers if record else [])}
    if not set(old_barriers).issubset({row["id"] for row in raw_barriers}):
        raise ValueError("Barrier history cannot be deleted. Resolve a barrier by securing its system.")
    barriers = []
    systems_by_id = {row["id"]: row for row in systems}
    for row in raw_barriers:
        old = old_barriers.get(row["id"], {})
        if old.get("status") == "resolved":
            if any(row.get(key) != value for key, value in old.items()):
                raise ValueError("Resolved barriers are immutable history.")
            barriers.append(old)
            continue
        system_id = text(row.get("systemLineId"), "Affected system", required=True)
        kind = text(row.get("type"), "Barrier type", required=True)
        if kind not in BARRIER_TYPES:
            raise ValueError("Choose a valid barrier type.")
        owner = text(row.get("owner"), "Barrier owner email", 254, True)
        try:
            validate_email(owner)
        except ValidationError:
            raise ValueError("Barrier owner must be a valid email address for reminders.")
        normalized = {
            "id": row["id"], "systemLineId": system_id, "type": kind, "owner": owner,
            "targetDate": date_value(row.get("targetDate"), "Target date", True),
            "description": text(row.get("description"), "Barrier description", 500, True),
            "status": "open", "resolvedAt": "",
            "systemName": next(
                (item["label"] for item in SYSTEM_CATALOGUE if item["id"] == systems_by_id.get(system_id, {}).get("systemId")), old.get("systemName", "Removed system")
            ),
            "lastNotifiedAt": old.get("lastNotifiedAt", ""),
        }
        if system_id not in systems_by_id or systems_by_id[system_id]["isSecured"]:
            if not old:
                raise ValueError("A new barrier must refer to an unsecured system.")
            normalized.update({"status": "resolved", "resolvedAt": timezone.now().isoformat()})
        barriers.append(normalized)
    if not permissions["edit"] and barriers != (record.barriers if record else []):
        raise PermissionError("Only the project lead or Access & Enablement administrator can change barriers.")
    for system in systems:
        if not system["isSecured"] and not any(row["systemLineId"] == system["id"] and row["status"] == "open" for row in barriers):
            raise ValueError("Every unsecured system requires a barrier record with owner, target date and description.")
    items = rows_list(payload.get("itItems"), "IT requirements", 5)
    if {item["id"] for item in items} != {item["id"] for item in IT_ITEMS}:
        raise ValueError("All five standard IT requirement items must be present.")
    items = [{"id": item["id"], "qtyConfirmed": integer(item.get("qtyConfirmed"), "Quantity confirmed")} for item in items]
    items.sort(key=lambda item: next(index for index, standard in enumerate(IT_ITEMS) if standard["id"] == item["id"]))
    previous_items = record.it_items if record and record.it_items else [{"id": item["id"], "qtyConfirmed": 0} for item in IT_ITEMS]
    old_quantities = {item["id"]: item["qtyConfirmed"] for item in previous_items}
    changed = any(item["qtyConfirmed"] != old_quantities.get(item["id"], 0) for item in items)
    if changed and not permissions["it"]:
        raise PermissionError("Only a locked GSC Leader / GSC Head-1 or Access & Enablement administrator can update IT quantities.")
    if source["ready"] and any(item["qtyConfirmed"] > source["population"] for item in items):
        raise ValueError("Confirmed quantities cannot exceed the locked Scope population.")
    previous_by_id = {item["id"]: item for item in previous_items}
    items = [
        {**item,
         "updatedBy": email if item["qtyConfirmed"] != old_quantities.get(item["id"], 0) else previous_by_id[item["id"]].get("updatedBy", ""),
         "updatedAt": timezone.now().isoformat() if item["qtyConfirmed"] != old_quantities.get(item["id"], 0) else previous_by_id[item["id"]].get("updatedAt", "")}
        for item in items
    ]
    confirmation = deepcopy(record.it_confirmation) if record else {}
    if changed or (confirmation and confirmation.get("sourceVersion") != source["version"]):
        confirmation = {}
    if payload.get("action") == "confirm_it":
        if not permissions["it"]:
            raise PermissionError("IT confirmation requires a locked GSC Leader / GSC Head-1 or Access & Enablement administrator.")
        if not source["ready"] or any(item["qtyConfirmed"] != source["population"] for item in items):
            raise ValueError("Every IT item must match the locked Scope population before confirmation.")
        confirmation = {
            "by": email, "at": timezone.now().isoformat(),
            "comment": text(payload.get("confirmationComment", ""), "IT confirmation comment", 2000),
            "sourceVersion": source["version"],
        }
    return systems, barriers, items, confirmation


@api_view(["GET", "POST"])
def project_artefact(request, project_id, kind):
    model = ProjectResources if kind == "resources" else AccessEnablement
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required."}, status=401)
    with transaction.atomic():
        projects = MigrationIntakeSubmission.objects
        if request.method == "POST":
            projects = projects.select_for_update()
        project = projects.filter(pk=project_id).first()
        if not project:
            return Response({"error": "Project not found."}, status=404)
        permissions = project_permissions(project, email, kind)
        if not permissions["view"]:
            return Response({"error": "Only the project requestor, Project Team or users with this artefact's access can view it."}, status=403)
        record = model.objects.filter(project=project).first()
        if request.method == "GET":
            return Response(_serialize(project, record, kind, email))
        payload = request.data
        if not isinstance(payload, dict):
            return Response({"error": "Request body must be an object."}, status=400)
        revision = payload.get("revision")
        source = scope_source(project)
        if type(revision) is not int or revision != (record.revision if record else 0) or payload.get("sourceVersion") != source["version"]:
            return Response({"error": "Project or Scope data changed. Reload before saving; your inputs have been retained."}, status=409)
        action = payload.get("action", "save")
        allowed = {"save", "submit", "reopen", "submit_area", "reopen_area"} if kind == "resources" else {"save", "submit", "reopen", "confirm_it"}
        if not isinstance(action, str) or action not in allowed:
            return Response({"error": "Unsupported artefact action."}, status=400)
        if not permissions["edit"] and not (kind == "access_enablement" and permissions["it"] and action in {"save", "confirm_it"}) and not (
            kind == "resources" and permissions["area"] and action in {"save", "submit_area", "reopen_area"}
        ):
            return Response({"error": "You do not have permission for this action."}, status=403)
        if record and record.status == "confirmed" and action != "reopen":
            return Response({"error": "Confirmed records are frozen. Reopen with a reason before editing."}, status=409)
        previous = {"status": record.status, "sourceVersion": record.source_version} if record else {}
        if record:
            fields = ("rows",) if kind == "resources" else ("systems", "barriers", "it_items", "it_confirmation")
            previous.update({key: deepcopy(getattr(record, key)) for key in fields})
        reason = ""
        try:
            if action in {"reopen", "reopen_area"}:
                reason = text(payload.get("reason"), "Revision reason", 2000, True)
            if action == "reopen":
                if not record or record.status != "confirmed":
                    raise ValueError("Only a confirmed record can be reopened.")
                record.status = "draft"
                if kind == "access_enablement":
                    record.it_confirmation = {}
            elif kind == "resources":
                rows = _resource_rows(payload, record, permissions, action, email)
                if any(row["site"] and row["site"] not in resource_sites(project) for row in rows):
                    raise ValueError("Choose a GSC site from the project or site catalogue.")
                if action == "submit" and not resource_ready(rows, source):
                    raise ValueError("Match locked Scope FTE, submit Area PIDs and complete onboarding / Efficiency details before confirming Resources.")
                if record is None:
                    record = model(project=project)
                record.rows = rows
                record.status = "confirmed" if action == "submit" else "draft"
            else:
                systems, barriers, items, confirmation = _access_data(payload, record, permissions, source, email)
                if action == "submit" and (
                    not access_summary(systems, barriers, items, confirmation, source)["ready"]
                    or any(not row["accessType"] or row["usersNeeded"] == 0 for row in systems)
                ):
                    raise ValueError("Record access types and users, secure all systems and confirm all IT items before submitting.")
                if record is None:
                    record = model(project=project)
                record.systems, record.barriers, record.it_items, record.it_confirmation = systems, barriers, items, confirmation
                record.status = "confirmed" if action == "submit" else "draft"
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        record.source_version = source["version"]
        record.revision += 1
        record.updated_by = email
        current = {"rows": record.rows} if kind == "resources" else {
            "systems": record.systems, "barriers": record.barriers,
            "it_items": record.it_items, "it_confirmation": record.it_confirmation,
        }
        current.update({"status": record.status, "sourceVersion": record.source_version})
        record.audit_log = [*record.audit_log, {
            "action": action, "by": email, "at": timezone.now().isoformat(),
            "revision": record.revision, "reason": reason, "old": previous, "new": current,
        }]
        record.save()
        return Response(_serialize(project, record, kind, email))


@api_view(["GET"])
def resource_projects(request):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required."}, status=401)
    projects = MigrationIntakeSubmission.objects.select_related("resources", "scope_statement").prefetch_related("scope_statement__lines")
    if not build_access_snapshot(email)["tables"]["resources"]:
        member_projects = [
            registration.project_id for registration in StakeholderRegistration.objects.only("project_id", "team_members")
            if any(normalize_email(person.get("email")) == email for person in registration.team_members)
        ]
        projects = projects.filter(Q(requestor__iexact=email) | Q(pk__in=member_projects))
    online = {case.project_id: case for case in BusinessCase.objects.only("project_id", "status", "review_required")}
    from api.views.approval_cycle import _progress
    legacy_progress = {
        workflow.migration_request_id: _progress(workflow)
        for workflow in ApprovalWorkflow.objects.all()
    }
    rows = []
    for project in projects.order_by("-id"):
        source = scope_source(project)
        case = online.get(project.pk)
        if case:
            approved = case.status == "submitted" and not case.review_required and bool(online_case_is_approved(project))
        else:
            progress = legacy_progress.get(project.migration_request_id)
            approved = bool(project.business_case_submission_date and progress and progress["step"] > progress["seqLen"] and progress["completed"])
        try:
            resource = project.resources
        except ProjectResources.DoesNotExist:
            resource = None
        population = source["population"]
        rows.append({
            "projectId": project.pk, "projectName": project.project_name,
            "migrationRequestId": project.migration_request_id, "products": project.products,
            "region": project.region, "areas": project.areas,
            "sites": (project.default_location_strategies or []) + (project.custom_location_strategies or []),
            "approvedFte": population if approved else None,
            "pipelineFte": population if not approved else None,
            "approvalStatus": "Approved" if approved else "Pipeline",
            "saved": bool(resource),
            "status": ("confirmed" if resource.source_version == source["version"] else "needs_review")
                      if resource and resource.status == "confirmed" else "draft" if resource else "not_started",
        })
    return Response({"rows": rows, "count": len(rows)})
