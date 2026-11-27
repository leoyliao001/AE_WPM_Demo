import copy
import math
import re
from datetime import date

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import (
    BaselineKpiRecord,
    MigrationIntakeSubmission,
    MigrationTeam,
    OpportunityAssessment,
    OpportunityAssessmentScope,
    ProjectResources,
    StakeholderRegistration,
)
from api.permissions.attributes_access import (
    build_access_snapshot,
    get_request_email,
    normalize_email,
)
from api.services.intake_options import INTAKE_OPTIONS
from api.services.project_artefacts import project_permissions

DIMENSIONS = [
    "Service",
    "Quality",
    "Governance",
    "Customer",
    "Operating Model",
    "Capacity",
]
MEASURES = [">=", "<=", "=", ">", "<"]
TARGET_BASELINES = {"Global", "Area"}
MAX_WEEKS = 10
DEFAULT_WEEKS = 4
MAX_EXTENSION_REASON_LENGTH = 2000
MAX_SETUP_UNLOCK_REASON_LENGTH = 2000
MAX_ADDITIONAL_COMMENTS_LENGTH = 500


def _current_cohorts(project):
    resource = ProjectResources.objects.filter(project=project).first()
    names = []
    seen = set()
    for row in (resource.rows if resource else []):
        if not isinstance(row, dict):
            continue
        name = str(row.get("cohort") or "").strip()
        if name and name not in seen:
            names.append(name)
            seen.add(name)
    return names


def _process_options(project):
    scope = OpportunityAssessmentScope.objects.filter(project=project).only("state").first()
    if scope:
        state = scope.state if isinstance(scope.state, dict) else {}
        mode = state.get("mode")
        if mode == "cat":
            groups = state.get("catGroups")
            if isinstance(groups, list) and groups:
                rows = [
                    row
                    for group in groups if isinstance(group, dict)
                    for row in (group.get("rows") or []) if isinstance(row, dict)
                ]
            else:
                rows = state.get("cat", [])
        elif mode == "task":
            rows = state.get("task", [])
        else:
            rows = []
        if not isinstance(rows, list):
            rows = []
    else:
        return sorted({
            str(value or "").strip()
            for value in OpportunityAssessment.objects.filter(
                migration_request_id=project.migration_request_id,
            ).values_list("l3", flat=True)
            if str(value or "").strip()
        })

    return sorted({
        str(row.get("l3") or "").strip()
        for row in rows
        if isinstance(row, dict) and str(row.get("l3") or "").strip()
    })


def _project_countries(project):
    areas_for_region = set(INTAKE_OPTIONS["regionAreaMapping"].get(project.region, []))
    areas = [
        area for area in (project.areas or [])
        if isinstance(area, str) and area in areas_for_region
    ]
    countries = {
        country
        for area in areas
        for country in INTAKE_OPTIONS["areaCountryMapping"].get(area, [])
    }
    return sorted(countries)


def _assigned_people(registration, role_code):
    if not registration:
        return []
    assignment = (registration.assignments or {}).get(role_code, {})
    if not isinstance(assignment, dict) or not assignment.get("lockedAt"):
        return []

    team_members = {
        str(person.get("id") or ""): person
        for person in (registration.team_members or [])
        if isinstance(person, dict)
    }
    managers = {
        f"migration-team-{manager.pk}": {
            "id": f"migration-team-{manager.pk}",
            "email": normalize_email(manager.email),
            "fullName": normalize_email(manager.email).split("@", 1)[0].replace(".", " ").title(),
        }
        for manager in MigrationTeam.objects.filter(role="Manager")
    }
    people = []
    person_ids = assignment.get("personIds", [])
    for person_id in person_ids if isinstance(person_ids, list) else []:
        person = team_members.get(str(person_id)) or managers.get(str(person_id))
        if not person:
            continue
        name = str(person.get("fullName") or "").strip()
        email = normalize_email(person.get("email"))
        label = name or email
        if label and label not in people:
            people.append(label)
    return people


def _role_emails(registration, role_code):
    if not registration:
        return set()
    assignment = (registration.assignments or {}).get(role_code, {})
    if not isinstance(assignment, dict) or not assignment.get("lockedAt"):
        return set()
    person_ids = {str(value) for value in assignment.get("personIds", [])}
    emails = {
        normalize_email(person.get("email"))
        for person in (registration.team_members or [])
        if isinstance(person, dict) and str(person.get("id") or "") in person_ids
    }
    if role_code == "migration_manager":
        emails.update(
            normalize_email(manager.email)
            for manager in MigrationTeam.objects.filter(role="Manager")
            if f"migration-team-{manager.pk}" in person_ids
        )
    return {email for email in emails if email}


def _permissions(project, email):
    registration = StakeholderRegistration.objects.filter(project=project).first()
    access = build_access_snapshot(email)
    setup_roles = set().union(
        _role_emails(registration, "area_poc"),
        _role_emails(registration, "area_sme"),
        _role_emails(registration, "migration_manager"),
    )
    migration_manager_roles = _role_emails(registration, "migration_manager")
    weekly_roles = set().union(
        _role_emails(registration, "gsc_sme"),
        _role_emails(registration, "gsc_leaders"),
        _role_emails(registration, "migration_manager"),
    )
    return {
        "view": bool(access.get("is_super_admin")) or project_permissions(project, email, "resources")["view"],
        "setup": bool(access.get("is_super_admin")) or email in setup_roles,
        "unlock": bool(access.get("is_super_admin")) or email in migration_manager_roles,
        "weekly": email in weekly_roles,
        "extend": email in weekly_roles,
        "people": {
            "areaPoc": _assigned_people(registration, "area_poc"),
            "areaSmes": _assigned_people(registration, "area_sme"),
            "gscSmes": _assigned_people(registration, "gsc_sme"),
            "gscLeaders": _assigned_people(registration, "gsc_leaders"),
            "migrationManagers": _assigned_people(registration, "migration_manager"),
        },
    }


def _default_kpi(index=1):
    return {
        "id": f"kpi-{index}",
        "process": [],
        "dimension": "",
        "kpi": "",
        "definition": "",
        "frequency": "Weekly",
        "globalTarget": None,
        "areaBaseline": None,
        "measure": ">=",
        "targetBaseline": "Area",
        "additionalComments": "",
        "weeklyValues": [None] * DEFAULT_WEEKS,
    }


def _cohort_data(name, stored, start_date):
    data = copy.deepcopy(stored) if isinstance(stored, dict) else {}
    weeks = data.get("weeks", DEFAULT_WEEKS)
    if isinstance(weeks, bool) or not isinstance(weeks, int) or not 1 <= weeks <= MAX_WEEKS:
        weeks = DEFAULT_WEEKS
    kpis = data.get("kpis")
    if not isinstance(kpis, list) or not kpis:
        kpis = [_default_kpi()]
    normalized_kpis = []
    for index, raw_kpi in enumerate(kpis, 1):
        if not isinstance(raw_kpi, dict):
            continue
        kpi = {**_default_kpi(index), **raw_kpi}
        raw_process = kpi.get("process")
        if isinstance(raw_process, str):
            raw_process = [raw_process]
        if not isinstance(raw_process, list):
            raw_process = []
        kpi["process"] = list(dict.fromkeys(
            value.strip()
            for value in raw_process
            if isinstance(value, str) and value.strip()
        ))
        values = kpi.get("weeklyValues")
        kpi["weeklyValues"] = (
            (values[:weeks] + [None] * weeks)[:weeks]
            if isinstance(values, list) else [None] * weeks
        )
        kpi.pop("comments", None)
        normalized_kpis.append(kpi)
    data.update({
        "name": name,
        "countries": data.get("countries", []) if isinstance(data.get("countries"), list) else [],
        "startDate": data.get("startDate") or start_date or "",
        "weeks": weeks,
        "setupSubmitted": bool(data.get("setupSubmitted")),
        "setupLocked": bool(data.get("setupSubmitted")) and bool(
            data.get("setupLocked", True)
        ),
        "kpis": normalized_kpis or [_default_kpi()],
        "extensionReasons": data.get("extensionReasons", []) if isinstance(data.get("extensionReasons"), list) else [],
        "setupUnlockHistory": (
            data.get("setupUnlockHistory", [])
            if isinstance(data.get("setupUnlockHistory"), list) else []
        ),
    })
    return data


def _strip_weekly_comments(state):
    cohorts = state.get("cohorts")
    if not isinstance(cohorts, dict):
        return state
    for cohort in cohorts.values():
        if not isinstance(cohort, dict):
            continue
        kpis = cohort.get("kpis")
        if not isinstance(kpis, list):
            continue
        for kpi in kpis:
            if isinstance(kpi, dict):
                kpi.pop("comments", None)
    return state


def _response(project, record, permissions):
    state = record.state if record and isinstance(record.state, dict) else {}
    stored_cohorts = state.get("cohorts", {})
    if not isinstance(stored_cohorts, dict):
        stored_cohorts = {}
    return {
        "projectId": project.pk,
        "projectName": project.project_name,
        "migrationRequestId": project.migration_request_id,
        "region": project.region,
        "areas": project.areas or [],
        "countries": _project_countries(project),
        "processOptions": _process_options(project),
        "revision": record.revision if record else 0,
        "updatedAt": record.updated_at.isoformat() if record else "",
        "updatedBy": record.updated_by if record else "",
        "permissions": permissions,
        "cohorts": [
            _cohort_data(name, stored_cohorts.get(name), project.target_start_date)
            for name in _current_cohorts(project)
        ],
    }


def _revision(value):
    if value is None or isinstance(value, bool) or not re.fullmatch(r"\d+", str(value)):
        raise ValueError("A valid baseline KPI revision is required.")
    return int(value)


def _int_field(value, label):
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a whole number.")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
        return int(value.strip())
    raise ValueError(f"{label} must be a whole number.")


def _validate_kpi(raw, index, weeks, process_options):
    if not isinstance(raw, dict):
        raise ValueError("Each KPI must be an object.")
    kpi_id = str(raw.get("id") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", kpi_id):
        raise ValueError("Each KPI requires a valid ID.")
    raw_process = raw.get("process")
    if not isinstance(raw_process, list) or not raw_process:
        raise ValueError(f"KPI {index}: select one or more valid Process values.")
    if any(not isinstance(value, str) for value in raw_process):
        raise ValueError(f"KPI {index}: select one or more valid Process values.")
    process = list(dict.fromkeys(value.strip() for value in raw_process if value.strip()))
    dimension = str(raw.get("dimension") or "").strip()
    name = str(raw.get("kpi") or "").strip()
    definition = str(raw.get("definition") or "").strip()
    additional_comments = raw.get("additionalComments", "")
    if not isinstance(additional_comments, str):
        raise ValueError(f"KPI {index}: Additional Comments must be text.")
    if len(additional_comments) > MAX_ADDITIONAL_COMMENTS_LENGTH:
        raise ValueError(
            f"KPI {index}: Additional Comments must be at most "
            f"{MAX_ADDITIONAL_COMMENTS_LENGTH} characters."
        )
    frequency = str(raw.get("frequency") or "").strip()
    measure = str(raw.get("measure") or "").strip()
    target_baseline = str(raw.get("targetBaseline") or "").strip()
    if not process or any(value not in process_options for value in process):
        raise ValueError(f"KPI {index}: select one or more valid Process values.")
    if dimension not in DIMENSIONS:
        raise ValueError(f"KPI {index}: select a valid Dimension.")
    if not name or len(name) > 50:
        raise ValueError(f"KPI {index}: enter a KPI name of at most 50 characters.")
    if not definition or len(definition) > 100:
        raise ValueError(f"KPI {index}: enter a definition of at most 100 characters.")
    if frequency != "Weekly":
        raise ValueError(f"KPI {index}: select a valid Frequency.")
    if measure not in MEASURES:
        raise ValueError(f"KPI {index}: select a valid Measure.")
    if target_baseline not in TARGET_BASELINES:
        raise ValueError(f"KPI {index}: select Global or Area for Target Baseline.")
    global_target = _int_field(raw.get("globalTarget"), "Global Target (%)")
    area_baseline = _int_field(raw.get("areaBaseline"), "Area Baseline (%)")
    values = raw.get("weeklyValues", [])
    return {
        "id": kpi_id,
        "process": process,
        "dimension": dimension,
        "kpi": name,
        "definition": definition,
        "frequency": frequency,
        "globalTarget": global_target,
        "areaBaseline": area_baseline,
        "measure": measure,
        "targetBaseline": target_baseline,
        "additionalComments": additional_comments,
        "weeklyValues": values if isinstance(values, list) and len(values) == weeks else [None] * weeks,
    }


def _validate_countries(project, cohort_names, stored_cohorts, name, countries):
    if not isinstance(countries, list) or not countries:
        raise ValueError(f"Select at least one country for {name}.")
    normalized_countries = list(dict.fromkeys(str(country).strip() for country in countries))
    invalid = set(normalized_countries) - set(_project_countries(project))
    if invalid:
        raise ValueError(
            f"{name} contains a country that is not available for this project's Region and Area."
        )
    other_countries = {
        country
        for other_name in cohort_names if other_name != name
        for country in _cohort_data(
            other_name,
            stored_cohorts.get(other_name),
            project.target_start_date,
        )["countries"]
    }
    if set(normalized_countries) & other_countries:
        raise ValueError("A country can only be assigned to one Cohort.")
    return normalized_countries


def _validate_additional_comments(raw_comments, current_kpis):
    if not isinstance(raw_comments, list) or len(raw_comments) != len(current_kpis):
        raise ValueError("Reload the page; the KPI rows changed.")
    current_by_id = {kpi["id"]: kpi for kpi in current_kpis}
    seen = set()
    result = []
    for raw in raw_comments:
        if not isinstance(raw, dict):
            raise ValueError("Each Additional Comments entry must be an object.")
        kpi_id = str(raw.get("id") or "")
        current = current_by_id.get(kpi_id)
        if not current or kpi_id in seen:
            raise ValueError("Reload the page; the KPI rows changed.")
        seen.add(kpi_id)
        comments = raw.get("additionalComments", "")
        if not isinstance(comments, str):
            raise ValueError("Additional Comments must be text.")
        if len(comments) > MAX_ADDITIONAL_COMMENTS_LENGTH:
            raise ValueError(
                f"Additional Comments must be at most {MAX_ADDITIONAL_COMMENTS_LENGTH} characters."
            )
        result.append({**current, "additionalComments": comments})
    return result


def _validate_weekly(kpis, current_kpis, weeks):
    if not isinstance(kpis, list) or len(kpis) != len(current_kpis):
        raise ValueError("Reload the page; the KPI rows changed.")
    current_by_id = {kpi["id"]: kpi for kpi in current_kpis}
    result = []
    seen = set()
    for raw in kpis:
        if not isinstance(raw, dict):
            raise ValueError("Each KPI result must be an object.")
        kpi_id = str(raw.get("id") or "")
        current = current_by_id.get(kpi_id)
        if not current or kpi_id in seen:
            raise ValueError("Reload the page; the KPI rows changed.")
        seen.add(kpi_id)
        values = raw.get("weeklyValues")
        if not isinstance(values, list) or len(values) != weeks:
            raise ValueError("Each KPI must contain a result for every week.")
        clean_values = []
        for week_index, value in enumerate(values):
            if value in (None, ""):
                clean_values.append(None)
            else:
                try:
                    number = float(value)
                except (TypeError, ValueError):
                    raise ValueError(f"Week {week_index + 1} must be a number.") from None
                if not math.isfinite(number):
                    raise ValueError(f"Week {week_index + 1} must be a finite number.")
                clean_values.append(str(value))
        result.append({**current, "weeklyValues": clean_values})
    return result


def _save_record(project, record, state, email):
    if record is None:
        record = BaselineKpiRecord(project=project)
    record.state = state
    record.revision += 1
    record.updated_by = email
    record.save()
    return record


@api_view(["GET", "PUT"])
def baseline_kpis(request, project_id):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=401)

    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if not project:
        return Response({"error": "Project not found."}, status=404)
    permissions = _permissions(project, email)
    if not permissions["view"]:
        return Response({"error": "Only project members and users with project access can view Baseline & KPIs."}, status=403)

    if request.method == "GET":
        record = BaselineKpiRecord.objects.filter(project=project).first()
        return Response(_response(project, record, permissions))

    action = str(request.data.get("action") or "")
    if action not in {"setup", "details", "unlock", "weekly", "extend"}:
        return Response({"error": "Choose a valid Baseline & KPI save action."}, status=400)
    if action in {"setup", "details"} and not permissions["setup"]:
        return Response({"error": "Only the assigned Area POC, Area SME, Migration Manager, or Super Admin can save KPI setup."}, status=403)
    if action == "unlock" and not permissions["unlock"]:
        return Response({"error": "Only the assigned Migration Manager or a Super Admin can unlock KPI setup."}, status=403)
    if action in {"weekly", "extend"} and not permissions["weekly"]:
        return Response({"error": "Only the assigned GSC SME, GSC Leaders, or Migration Manager can update weekly results or extend Hypercare."}, status=403)

    try:
        revision = _revision(request.data.get("revision"))
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)

    with transaction.atomic():
        project = MigrationIntakeSubmission.objects.select_for_update().filter(pk=project_id).first()
        if not project:
            return Response({"error": "Project not found."}, status=404)
        permissions = _permissions(project, email)
        if action in {"setup", "details"} and not permissions["setup"]:
            return Response({"error": "Only the assigned Area POC, Area SME, Migration Manager, or Super Admin can save KPI setup."}, status=403)
        if action == "unlock" and not permissions["unlock"]:
            return Response({"error": "Only the assigned Migration Manager or a Super Admin can unlock KPI setup."}, status=403)
        if action in {"weekly", "extend"} and not permissions["weekly"]:
            return Response({"error": "Only the assigned GSC SME, GSC Leaders, or Migration Manager can update weekly results or extend Hypercare."}, status=403)
        record = BaselineKpiRecord.objects.select_for_update().filter(project=project).first()
        current_revision = record.revision if record else 0
        if revision != current_revision:
            return Response({"error": "Baseline & KPI data changed since it was loaded. Reload before saving."}, status=409)

        old_state = _strip_weekly_comments(
            copy.deepcopy(record.state) if record and isinstance(record.state, dict) else {}
        )
        stored_cohorts = old_state.get("cohorts", {})
        if not isinstance(stored_cohorts, dict):
            stored_cohorts = {}
        cohort_names = _current_cohorts(project)

        try:
            if action == "setup":
                item = request.data.get("cohort")
                if not isinstance(item, dict):
                    raise ValueError("Cohort setup data is required.")
                name = str(item.get("name") or "").strip()
                if name not in cohort_names:
                    raise ValueError("Resource Cohorts changed. Reload this page before saving.")
                existing = _cohort_data(name, stored_cohorts.get(name), project.target_start_date)
                if existing["setupSubmitted"] and existing["setupLocked"]:
                    raise ValueError(
                        "KPI setup is locked. A Migration Manager or Super Admin must unlock it before editing."
                    )
                normalized_countries = _validate_countries(
                    project,
                    cohort_names,
                    stored_cohorts,
                    name,
                    item.get("countries"),
                )
                start_date = str(item.get("startDate") or "").strip()
                if start_date:
                    try:
                        date.fromisoformat(start_date)
                    except ValueError:
                        raise ValueError(f"{name}: start date must use YYYY-MM-DD format.") from None
                weeks = existing["weeks"]
                raw_kpis = item.get("kpis")
                if not isinstance(raw_kpis, list) or not raw_kpis or len(raw_kpis) > 100:
                    raise ValueError(f"{name}: add at least one KPI row (maximum 100).")
                process_options = _process_options(project)
                kpis = [
                    _validate_kpi(raw, index, weeks, process_options)
                    for index, raw in enumerate(raw_kpis, 1)
                ]
                if len({kpi["id"] for kpi in kpis}) != len(kpis):
                    raise ValueError(f"{name}: KPI row IDs must be unique.")
                old_kpis = {kpi.get("id"): kpi for kpi in existing["kpis"]}
                for kpi in kpis:
                    old_kpi = old_kpis.get(kpi["id"], {})
                    kpi["weeklyValues"] = old_kpi.get("weeklyValues", [None] * weeks)
                stored_cohorts[name] = {
                    **existing,
                    "countries": normalized_countries,
                    "startDate": start_date or existing["startDate"],
                    "setupSubmitted": True,
                    "setupLocked": True,
                    "kpis": kpis,
                }

            elif action == "details":
                item = request.data.get("cohort")
                if not isinstance(item, dict):
                    raise ValueError("Cohort details are required.")
                name = str(item.get("name") or "").strip()
                if name not in cohort_names:
                    raise ValueError("Resource Cohorts changed. Reload this page before saving.")
                existing = _cohort_data(name, stored_cohorts.get(name), project.target_start_date)
                if not existing["setupSubmitted"]:
                    raise ValueError("Save the KPI setup before saving Cohort details.")
                normalized_countries = _validate_countries(
                    project,
                    cohort_names,
                    stored_cohorts,
                    name,
                    item.get("countries"),
                )
                start_date = str(item.get("startDate") or "").strip()
                if start_date:
                    try:
                        date.fromisoformat(start_date)
                    except ValueError:
                        raise ValueError(f"{name}: start date must use YYYY-MM-DD format.") from None
                kpis = _validate_additional_comments(
                    item.get("kpis"),
                    existing["kpis"],
                )
                stored_cohorts[name] = {
                    **existing,
                    "countries": normalized_countries,
                    "startDate": start_date or existing["startDate"],
                    "kpis": kpis,
                }

            elif action == "unlock":
                name = str(request.data.get("cohortName") or "").strip()
                if name not in cohort_names:
                    raise ValueError("The selected Cohort no longer exists in Resources.")
                existing = _cohort_data(name, stored_cohorts.get(name), project.target_start_date)
                if not existing["setupSubmitted"]:
                    raise ValueError("Save the KPI setup before unlocking it.")
                if not existing["setupLocked"]:
                    raise ValueError("KPI setup is already unlocked.")
                reason = str(request.data.get("reason") or "").strip()
                if not reason:
                    raise ValueError("An unlock reason is required.")
                if len(reason) > MAX_SETUP_UNLOCK_REASON_LENGTH:
                    raise ValueError("The unlock reason is too long.")
                existing["setupLocked"] = False
                existing["setupUnlockHistory"].append({
                    "reason": reason,
                    "unlockedAt": timezone.now().isoformat(),
                    "by": email,
                })
                stored_cohorts[name] = existing

            elif action == "weekly":
                name = str(request.data.get("cohortName") or "").strip()
                if name not in cohort_names:
                    raise ValueError("The selected Cohort no longer exists in Resources.")
                existing = _cohort_data(name, stored_cohorts.get(name), project.target_start_date)
                if not existing["setupSubmitted"]:
                    raise ValueError("Save the KPI setup before entering weekly results.")
                kpis = _validate_weekly(
                    request.data.get("kpis"),
                    existing["kpis"],
                    existing["weeks"],
                )
                stored_cohorts[name] = {**existing, "kpis": kpis}

            elif action == "extend":
                name = str(request.data.get("cohortName") or "").strip()
                if name not in cohort_names:
                    raise ValueError("The selected Cohort no longer exists in Resources.")
                existing = _cohort_data(name, stored_cohorts.get(name), project.target_start_date)
                if not existing["setupSubmitted"]:
                    raise ValueError("Save the KPI setup before extending Hypercare.")
                reason = str(request.data.get("reason") or "").strip()
                if not reason:
                    raise ValueError("An extension reason is required.")
                if len(reason) > MAX_EXTENSION_REASON_LENGTH:
                    raise ValueError("The extension reason is too long.")
                additional_weeks = _int_field(request.data.get("additionalWeeks"), "Additional weeks")
                if additional_weeks < 1 or existing["weeks"] + additional_weeks > MAX_WEEKS:
                    raise ValueError(f"Hypercare must not exceed {MAX_WEEKS} total weeks.")
                new_total = existing["weeks"] + additional_weeks
                for kpi in existing["kpis"]:
                    kpi["weeklyValues"] = (kpi["weeklyValues"] + [None] * additional_weeks)[:new_total]
                existing["weeks"] = new_total
                existing["extensionReasons"].append({
                    "reason": reason,
                    "additionalWeeks": additional_weeks,
                    "extendedAt": date.today().isoformat(),
                    "by": email,
                })
                stored_cohorts[name] = existing
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)

        state = {**old_state, "cohorts": stored_cohorts}
        record = _save_record(project, record, state, email)

    return Response(_response(project, record, _permissions(project, email)))
