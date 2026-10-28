import hashlib
import json
import re
from copy import deepcopy

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from api.models import OpportunityAssessment, ScopeStatement, StakeholderRegistration
from api.permissions.attributes_access import build_access_snapshot, normalize_email
from api.services.project_artefacts import date_value, rows_list, scope_source, text

REVIEW_ROLES = {
    "migration": {"label": "Migration", "codes": ["wpm_focals"]},
    "area": {"label": "Area", "codes": ["area_poc", "area_sme"]},
    "execution": {"label": "Execution", "codes": ["gsc_leaders", "gsc_head_1"]},
    "resilience": {"label": "Business Resilience", "codes": ["business_resilience"]},
}
FLAG_LABELS = {
    "critical": "Critical", "single_site": "Single-site", "system_sensitive": "System-sensitive",
    "backlog_prone": "Backlog-prone", "complex": "Complex", "crisis_impacting": "Crisis-impacting",
    "second_site": "Second site recommended",
}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
APPLICATIONS = ["SAP", "Salesforce", "ServiceNow", "SharePoint", "Documentation system", "Outlook / shared mailbox"]


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def context(project, email):
    registration = StakeholderRegistration.objects.filter(project=project).first()
    members = registration.team_members if registration else []
    assignments = registration.assignments if registration else {}
    reviewers = {}
    for role, definition in REVIEW_ROLES.items():
        ids = {
            person for code in definition["codes"]
            for person in assignments.get(code, {}).get("personIds", [])
            if assignments.get(code, {}).get("lockedAt") and not assignments.get(code, {}).get("notApplicable")
        }
        reviewers[role] = [
            {"id": person["id"], "name": person["fullName"], "email": normalize_email(person["email"])}
            for person in members if person["id"] in ids
        ]
    admin = bool(build_access_snapshot(email)["tables"].get("business_impact_analysis"))
    lead = email == normalize_email(project.requestor) or any(person["email"] == email for person in reviewers["migration"])
    area = any(person["email"] == email for person in reviewers["area"])
    permissions = {
        "admin": admin, "view": admin or lead or any(normalize_email(person.get("email")) == email for person in members),
        "edit": admin or lead or area,
        "reviewRoles": [role for role, people in reviewers.items() if any(person["email"] == email for person in people)],
    }
    scope = ScopeStatement.objects.filter(project=project).first()
    source = {
        **scope_source(project), "verticals": project.products,
        "region": project.region, "areas": project.areas,
        "sites": list(dict.fromkeys((project.default_location_strategies or []) + (project.custom_location_strategies or []))),
        "subprocesses": scope.scope_text if scope else "",
        "languageDependencies": project.language_dependencies,
        "reviewers": reviewers,
        "reviewAssignments": {
            code: {key: assignments.get(code, {}).get(key) for key in ("personIds", "lockedAt", "lockedBy", "notApplicable")}
            for definition in REVIEW_ROLES.values() for code in definition["codes"]
        },
    }
    processes = {}
    for row in OpportunityAssessment.objects.filter(migration_request_id=project.migration_request_id).order_by("id"):
        if not row.l3.strip():
            continue
        path = [row.l1.strip(), row.l2.strip(), row.l3.strip()]
        key = fingerprint(path)[:24]
        processes.setdefault(key, {
            "id": key, "name": path[-1], "path": " / ".join(part for part in path if part),
            "origin": "Opportunity Assessment / Task details", "activities": [],
        })
        activity = row.l4.strip() or row.task_name.strip()
        if activity and activity not in processes[key]["activities"]:
            processes[key]["activities"].append(activity)
    if not processes:
        # Intake / Scope are free text today; never infer several processes by splitting prose.
        processes["intake-scope"] = {
            "id": "intake-scope", "name": project.function_name.strip() or project.project_name,
            "path": project.function_name.strip() or project.project_name,
            "origin": "Intake function (project-wide fallback)", "activities": [],
        }
    source["processes"] = list(processes.values())
    source["version"] = fingerprint({key: value for key, value in source.items() if key != "version"})
    return source, permissions


def empty_questionnaire(process_id):
    return {"id": process_id, "answers": {}, "flags": [], "mitigations": [], "status": "draft", "reviews": {}}


def normalize_answers(raw):
    if not isinstance(raw, dict):
        raise ValueError("Answers must be an object.")
    result = {
        key: text(raw.get(key, ""), label, limit)
        for key, label, limit in [
            ("processType", "Process type", 20), ("sla", "SLA", 2000),
            ("peakDays", "Peak volume days", 500), ("peakMonths", "Peak volume months", 500),
            ("languageFte", "Language-dependent FTE (or None)", 500),
            ("startUtc", "Start time", 5), ("endUtc", "End time", 5),
            ("currentGsc", "Current GSC", 500), ("secondSite", "Second-site recommendation", 10),
            ("secondSiteReason", "Second-site rationale", 2000),
            ("retainSupport", "Contingency support", 10), ("retainedDetails", "Retained support details", 2000),
            ("otherInformation", "Other BCP information (or None)", 4000),
        ]
    }
    for key, choices in [("processType", {"", "new", "existing"}), ("secondSite", {"", "yes", "no", "maybe"}), ("retainSupport", {"", "yes", "no"})]:
        if result[key] not in choices:
            raise ValueError(f"Choose a valid {key} option.")
    for key in ("startUtc", "endUtc"):
        if result[key] and not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", result[key]):
            raise ValueError("Operating times must use HH:MM in UTC.")
    days = raw.get("operatingDays", [])
    if not isinstance(days, list) or any(day not in DAYS for day in days) or len(days) != len(set(days)):
        raise ValueError("Choose unique operating days from the list.")
    apps = raw.get("applications", [])
    if not isinstance(apps, list) or len(apps) > 50:
        raise ValueError("Applications must be a list of at most 50 names.")
    apps = [text(app, "Application", 128, True) for app in apps]
    if len({app.casefold() for app in apps}) != len(apps):
        raise ValueError("Application names must be unique.")
    result.update({"operatingDays": days, "applications": apps})
    if result["processType"] == "new":
        result["currentGsc"] = ""
    if result["retainSupport"] != "yes":
        result["retainedDetails"] = ""
    return result


def owner_date(row, label):
    owner = text(row.get("owner", ""), f"{label} owner", 254)
    if owner:
        try:
            validate_email(owner)
        except ValidationError:
            raise ValueError(f"{label} owner must be a valid email address.")
    return {"owner": owner.lower(), "dueDate": date_value(row.get("dueDate", ""), f"{label} target date")}


def normalize_questionnaire(raw, source, previous):
    answers = normalize_answers(raw.get("answers", {}))
    flags = []
    for flag in rows_list(raw.get("flags", []), "Attention flags", len(FLAG_LABELS)):
        if flag["id"] not in FLAG_LABELS:
            raise ValueError("Choose an attention flag from the list.")
        if flag["id"] != "second_site" or answers["secondSite"] in {"yes", "maybe"}:
            flags.append({"id": flag["id"], **owner_date(flag, "Attention flag")})
    if answers["secondSite"] in {"yes", "maybe"} and not any(flag["id"] == "second_site" for flag in flags):
        flags.append({"id": "second_site", "owner": "", "dueDate": ""})
    mitigations = []
    for action in rows_list(raw.get("mitigations", []), "Mitigation actions", 100):
        state = action.get("status", "open")
        if state not in {"open", "completed"}:
            raise ValueError("Mitigation status must be open or completed.")
        mitigations.append({
            "id": action["id"], "description": text(action.get("description", ""), "Mitigation description", 2000),
            **owner_date(action, "Mitigation action"), "status": state,
        })
    return {
        "id": raw["id"], "answers": answers, "flags": flags, "mitigations": mitigations,
        "status": previous["status"], "reviews": deepcopy(previous["reviews"]),
    }


def completion(questionnaire, process, source):
    a = questionnaire["answers"]
    answered = [
        bool(a.get("processType")),
        bool(process["name"] and source["verticals"] and source["subprocesses"]),
        all(a.get(key) for key in ("sla", "peakDays", "peakMonths")) and bool(source["region"]),
        source["ready"] and bool(a.get("languageFte")),
        all(a.get(key) for key in ("startUtc", "endUtc", "operatingDays")),
        bool(a.get("applications")),
        bool(source["sites"]) and (a.get("processType") == "new" or bool(a.get("currentGsc"))),
        bool(a.get("secondSite")),
        a.get("retainSupport") == "no" or a.get("retainSupport") == "yes" and bool(a.get("retainedDetails")),
        bool(a.get("otherInformation")),
    ]
    blockers = [f"Q{i + 1}" for i, done in enumerate(answered) if not done]
    if any(not flag["owner"] or not flag["dueDate"] for flag in questionnaire["flags"]):
        blockers.append("Attention flag owner / target date")
    if any(not all(action[key] for key in ("description", "owner", "dueDate")) for action in questionnaire["mitigations"]):
        blockers.append("Mitigation description / owner / target date")
    if questionnaire["flags"] and not questionnaire["mitigations"]:
        blockers.append("At least one mitigation action for flagged risks")
    return {"answered": sum(bool(item) for item in answered), "questions": answered, "blockers": blockers}


def effective_questionnaire(raw, process, source, changed):
    result = deepcopy(raw or empty_questionnaire(process["id"]))
    if changed:
        result["status"] = "needs_review" if result["status"] != "draft" else "draft"
        result["reviews"] = {}
    result.update({"process": process, "progress": completion(result, process, source)})
    return result
