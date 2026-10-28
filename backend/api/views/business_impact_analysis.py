from copy import deepcopy

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import BusinessImpactAnalysis, MigrationIntakeSubmission
from api.permissions.attributes_access import get_request_email, normalize_email
from api.services.business_impact_analysis import (
    APPLICATIONS, DAYS, FLAG_LABELS, REVIEW_ROLES, completion, context,
    effective_questionnaire, empty_questionnaire, normalize_questionnaire,
)
from api.services.project_artefacts import text


def serialize(project, record, source, permissions):
    changed = bool(record and record.source_version != source["version"])
    questionnaires = [
        effective_questionnaire((record.questionnaires if record else {}).get(process["id"]), process, source, changed)
        for process in source["processes"]
    ]
    all_signed = all(item["status"] == "signed_off" for item in questionnaires)
    return {
        "projectId": project.pk, "projectName": project.project_name, "migrationRequestId": project.migration_request_id,
        "revision": record.revision if record else 0, "source": source, "sourceChanged": changed,
        "permissions": permissions, "saved": record is not None, "questionnaires": questionnaires,
        "status": "confirmed" if all_signed else "needs_review" if changed and record else
                  "in_review" if any(item["status"] == "submitted" for item in questionnaires) else "draft",
        "ready": all_signed, "updatedAt": record.updated_at.isoformat() if record else "",
        "updatedBy": record.updated_by if record else "", "auditLog": record.audit_log if record else [],
        "flagLabels": FLAG_LABELS, "reviewRoles": REVIEW_ROLES, "days": DAYS, "applications": APPLICATIONS,
        "archivedCount": len(set(record.questionnaires) - {process["id"] for process in source["processes"]}) if record else 0,
    }


@api_view(["GET", "POST"])
def business_impact_analysis(request, project_id):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required."}, status=401)
    with transaction.atomic():
        projects = MigrationIntakeSubmission.objects.select_for_update() if request.method == "POST" else MigrationIntakeSubmission.objects
        project = projects.filter(pk=project_id).first()
        if not project:
            return Response({"error": "Project not found."}, status=404)
        source, permissions = context(project, email)
        if not permissions["view"]:
            return Response({"error": "Only the project team or Business Impact Analysis administrators can view this questionnaire."}, status=403)
        record = BusinessImpactAnalysis.objects.filter(project=project).first()
        if request.method == "GET":
            return Response(serialize(project, record, source, permissions))
        payload = request.data
        if not isinstance(payload, dict):
            return Response({"error": "Request body must be an object."}, status=400)
        if type(payload.get("revision")) is not int or payload["revision"] != (record.revision if record else 0) or payload.get("sourceVersion") != source["version"]:
            return Response({"error": "Questionnaire or source data changed. Reload before saving; your inputs are retained."}, status=409)
        action = payload.get("action", "save")
        if not isinstance(action, str) or action not in {"save", "submit", "review", "sign_off", "reopen"}:
            return Response({"error": "Unsupported BIA action."}, status=400)
        if action in {"save", "submit", "reopen"} and not permissions["edit"]:
            return Response({"error": "Only the Requestor, locked WPM / Area team or BIA administrators can edit."}, status=403)
        process = next((item for item in source["processes"] if item["id"] == payload.get("processId")), None)
        if process is None:
            return Response({"error": "Select an active process."}, status=400)
        previous = deepcopy(record.questionnaires) if record else {}
        changed = bool(record and record.source_version != source["version"])
        current = effective_questionnaire(previous.get(process["id"]), process, source, changed)
        reason = ""
        try:
            if action == "reopen":
                if current["status"] == "draft":
                    raise ValueError("Only a submitted, signed-off or outdated questionnaire can be reopened.")
                reason = text(payload.get("reason"), "Reopen reason", 2000, True)
                updated = {key: deepcopy(current[key]) for key in ("id", "answers", "flags", "mitigations")}
                updated.update({"status": "draft", "reviews": {}})
            elif action in {"save", "submit"}:
                if current["status"] in {"submitted", "signed_off"}:
                    return Response({"error": "Reopen this questionnaire with a reason before editing."}, status=409)
                raw = payload.get("questionnaire")
                if not isinstance(raw, dict) or raw.get("id") != process["id"]:
                    raise ValueError("Questionnaire must match the selected process.")
                updated = normalize_questionnaire(raw, source, empty_questionnaire(process["id"]))
                progress = completion(updated, process, source)
                if action == "submit" and progress["blockers"]:
                    raise ValueError("Complete before submitting: " + ", ".join(progress["blockers"]) + ".")
                updated["status"] = "submitted" if action == "submit" else "draft"
                if action == "submit":
                    updated.update({"submittedBy": email, "submittedAt": timezone.now().isoformat()})
            else:
                if current["status"] != "submitted" or completion(current, process, source)["blockers"]:
                    raise ValueError("Submit a complete, current questionnaire before review or sign-off.")
                updated = {key: deepcopy(value) for key, value in current.items() if key not in {"process", "progress"}}
                if action == "review":
                    role = payload.get("reviewRole")
                    if not isinstance(role, str) or role not in REVIEW_ROLES:
                        raise ValueError("Choose a joint-review role.")
                    if not source["reviewers"][role]:
                        raise ValueError("Assign and lock a reviewer in Stakeholder Registration first.")
                    if role not in permissions["reviewRoles"] and not permissions["admin"]:
                        return Response({"error": "Only the locked reviewer for this role or a BIA administrator can record its review."}, status=403)
                    if role in updated["reviews"]:
                        raise ValueError("This review is already recorded. Reopen to revise it.")
                    updated["reviews"][role] = {
                        "by": email, "at": timezone.now().isoformat(),
                        "comment": text(payload.get("comment", ""), "Review comment", 2000),
                        "sourceVersion": source["version"], "adminOverride": role not in permissions["reviewRoles"],
                    }
                else:
                    if not permissions["admin"] and not set(permissions["reviewRoles"]).intersection({"area", "execution"}):
                        return Response({"error": "Area, Execution or a BIA administrator must perform final sign-off."}, status=403)
                    if not all(updated["reviews"].get(role, {}).get("sourceVersion") == source["version"] for role in REVIEW_ROLES):
                        raise ValueError("All four joint reviews, including Area and Execution, are required before final sign-off.")
                    updated.update({"status": "signed_off", "signedOffBy": email, "signedOffAt": timezone.now().isoformat()})
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        if record is None:
            record = BusinessImpactAnalysis(project=project)
        if changed:
            # Keep removed-process records for audit; invalidate every active process, not only the edited one.
            for item in record.questionnaires.values():
                item["status"] = "needs_review" if item["status"] != "draft" else "draft"
                item["reviews"] = {}
        record.questionnaires[process["id"]] = updated
        record.revision += 1
        record.audit_log = [*record.audit_log, {
            "action": action, "processId": process["id"], "by": email, "at": timezone.now().isoformat(),
            "revision": record.revision, "reason": reason, "old": {"questionnaires": previous, "source": record.source_snapshot},
            "new": {"questionnaires": deepcopy(record.questionnaires), "source": source},
        }]
        record.source_snapshot = source
        record.source_version = source["version"]
        record.updated_by = email
        record.save()
        return Response(serialize(project, record, source, permissions))
