import hashlib
import json
from datetime import date

from api.models import ScopeStatement, StakeholderRegistration
from api.permissions.attributes_access import build_access_snapshot, normalize_email
from api.services.intake_options import INTAKE_OPTIONS

SYSTEM_CATALOGUE = [
    {"id": "salesforce", "label": "Salesforce"},
    {"id": "sap", "label": "SAP ECC (FI-AR)"},
    {"id": "servicenow", "label": "ServiceNow"},
    {"id": "sharepoint", "label": "SharePoint"},
    {"id": "booking", "label": "Local booking tool"},
    {"id": "other", "label": "Other system (specify access / licence type)"},
]
IT_ITEMS = [
    {"id": "laptop", "label": "Laptops (standard build)"},
    {"id": "headset", "label": "Headsets"},
    {"id": "monitor", "label": "Second monitors"},
    {"id": "vpn", "label": "VPN & network access"},
    {"id": "mfa", "label": "MFA token / authenticator"},
]
BARRIER_TYPES = ["Licensing", "Permissions", "Hardware", "Network", "Security", "Other"]
HIRING_TYPES = ["External", "IJP", "Efficiency"]
HIRING_STATUSES = ["Pending", "In Progress", "At Risk", "Onboarded"]
LANGUAGES = ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Danish", "Dutch", "Other"]
EXECUTION_FIELDS = ["site", "hiringType", "language", "pidCreationDate", "gscPid", "deletedPid"]
AREA_FIELDS = ["region", "area", "country", "areaPid", "areaApmmId", "releaseDate"]
HR_FIELDS = ["requisitionId", "hiringStatus", "remarks", "tentativeDoj", "actualDoj", "apmmId"]


def resource_sites(project):
    return sorted(set(
        (project.default_location_strategies or []) + (project.custom_location_strategies or []) +
        INTAKE_OPTIONS["customLocationStrategyOptions"] +
        [site for area in INTAKE_OPTIONS["areaLocationMapping"].values() for site in area.get("supportingSites", [])]
    ))


def project_permissions(project, email, key):
    access = build_access_snapshot(email)
    admin = bool(access["tables"].get(key))
    registration = StakeholderRegistration.objects.filter(project=project).first()
    members = registration.team_members if registration else []
    own_ids = {person["id"] for person in members if normalize_email(person.get("email")) == email}
    roles = {
        code for code, assignment in (registration.assignments if registration else {}).items()
        if assignment.get("lockedAt") and own_ids.intersection(assignment.get("personIds", []))
    }
    lead = admin or email == normalize_email(project.requestor) or "wpm_focals" in roles
    return {
        "view": admin or lead or bool(own_ids),
        "edit": lead,
        "area": lead or "area_poc" in roles,
        "it": admin or bool(roles.intersection({"gsc_leaders", "gsc_head_1"})),
    }


def scope_source(project):
    try:
        scope = project.scope_statement
    except ScopeStatement.DoesNotExist:
        scope = None
    lines = list(scope.lines.all()) if scope else []
    ready = bool(
        scope and scope.status == "submitted" and not scope.review_required
        and scope.final_project_fte is not None
        and {line.job_level for line in lines} == {"JL2", "JL3", "JL4"}
        and all(line.locked_at and line.final_fte is not None for line in lines)
        and sum(line.final_fte for line in lines) == scope.final_project_fte
    )
    basis = {
        "scopeRevision": scope.revision if scope else 0,
        "status": scope.status if scope else "missing",
        "reviewRequired": scope.review_required if scope else False,
        "population": scope.final_project_fte if ready else None,
    }
    version = hashlib.sha256(json.dumps(basis, sort_keys=True).encode()).hexdigest()
    return {**basis, "ready": ready, "version": version}


def text(value, label, limit=500, required=False):
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValueError(f"{label} must be {'non-empty ' if required else ''}text of at most {limit} characters.")
    return value.strip()


def integer(value, label):
    if type(value) is not int or not 0 <= value <= 100000:
        raise ValueError(f"{label} must be a whole number between 0 and 100000.")
    return value


def date_value(value, label, required=False):
    value = text(value, label, 10, required)
    if value:
        try:
            if date.fromisoformat(value).isoformat() != value:
                raise ValueError
        except ValueError:
            raise ValueError(f"{label} must be a valid YYYY-MM-DD date.")
    return value


def rows_list(value, label, limit=1000):
    if not isinstance(value, list) or len(value) > limit or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{label} must be a list of at most {limit} records.")
    ids = [row.get("id") for row in value]
    if any(not isinstance(key, str) or not key or len(key) > 80 for key in ids) or len(set(ids)) != len(ids):
        raise ValueError(f"{label} must have unique non-empty IDs.")
    return value


def resource_ready(rows, source):
    return bool(source["ready"] and len(rows) == source["population"] and all(
        row.get("site") and row.get("language") and row.get("gscPid") and row.get("pidCreationDate")
        and row.get("areaLockedAt") and row.get("actualDoj") and row.get("apmmId")
        and (row.get("hiringType") == "Efficiency" and row.get("deletedPid")
             or row.get("hiringType") != "Efficiency" and row.get("hiringStatus") == "Onboarded" and row.get("requisitionId"))
        for row in rows
    ))


def access_summary(systems, barriers, items, confirmation, source):
    secured = sum(line["isSecured"] for line in systems)
    complete = sum(item["qtyConfirmed"] == source["population"] for item in items) if source["ready"] else 0
    all_secured = bool(systems) and secured == len(systems)
    it_confirmed = bool(confirmation.get("at") and confirmation.get("sourceVersion") == source["version"] and complete == len(IT_ITEMS))
    return {
        "secured": secured, "systems": len(systems), "allAccessSecured": all_secured,
        "openBarriers": sum(barrier["status"] == "open" for barrier in barriers),
        "overdueBarriers": sum(barrier["status"] == "open" and barrier["targetDate"] < date.today().isoformat() for barrier in barriers),
        "itComplete": complete, "itConfirmed": it_confirmed,
        "ready": source["ready"] and all_secured and it_confirmed,
    }
