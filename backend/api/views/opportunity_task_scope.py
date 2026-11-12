import copy
import json
import re
from functools import lru_cache

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationIntakeSubmission, OpportunityAssessment, OpportunityAssessmentScope, ServiceCatalogue, StakeholderRegistration
from api.permissions.attributes_access import get_request_email
from api.views.opportunity_assessment import _build_setup_context, _deny_unless_requestor, _get_project, _parse_number
from api.views.fpo_catalogue_requests import catalogue_request_reminders
from api.views.stakeholder_registration import _assigned_role_emails


FIELD_MAP = {
    "p": "product", "loc": "location", "l1": "l1", "l2": "l2", "l3": "l3", "l4": "l4",
    "task": "task_name", "desc": "task_description", "mig": "migratable_to_gsc",
    "cx": "complexity", "sop": "sop_iop_exists", "freq": "task_frequency",
    "uom": "unit_of_measure", "vol": "volume_monthly", "tpu": "task_time_per_unit_min",
}
FREQUENCIES = {"Daily": 21, "Weekly": 4.33, "Monthly": 1, "Quarterly": 1 / 3, "Yearly": 1 / 12, "Ad hoc": 1}
LEGACY_FIELDS = ("upstream", "downstream", "risks_related", "training_time_needed", "recommended_handoff_duration")
OPTIONS = {
    "cx": {"", "Low", "Medium", "High"}, "sop": {"", "Y", "N"},
    "freq": {"", *FREQUENCIES}, "mgsc": {"", "Yes", "No"},
    "exc": {"", "Language Barrier", "Legal Issues", "Already in GSC"},
}


@lru_cache(maxsize=1)
def _base_catalogue():
    source = (settings.BASE_DIR.parent / "refer doc" / "WPM_Pulse_OA_Task_Scoping.html").read_text(encoding="utf-8")
    return json.JSONDecoder().raw_decode(source.split("const CAT=", 1)[1])[0]


@lru_cache(maxsize=1)
def _catalogue_additions():
    catalogue = _base_catalogue()
    keys = {tuple(str(value).strip().casefold() for value in row[:5]) for row in catalogue}
    additions = []
    for row in ServiceCatalogue.objects.all().values("product", "l1", "l2", "l3", "l4", "current_ownership"):
        hierarchy = tuple(str(row[field] or "").strip() for field in ("product", "l1", "l2", "l3", "l4"))
        key = tuple(value.casefold() for value in hierarchy)
        if not all(hierarchy) or key in keys:
            continue
        additions.append([*hierarchy, "", row["current_ownership"] or "", "", hierarchy[4]])
        keys.add(key)
    return additions


@lru_cache(maxsize=1)
def _catalogue():
    return _base_catalogue() + _catalogue_additions()


def _initial_state(project):
    tasks = []
    catalogue = _catalogue()
    refs = {tuple(item[:5]): index for index, item in enumerate(catalogue)}
    for item in OpportunityAssessment.objects.filter(migration_request_id=project.migration_request_id):
        row = {key: getattr(item, field) for key, field in FIELD_MAP.items()}
        row["sop"] = {"yes": "Y", "no": "N", "y": "Y", "n": "N"}.get(row["sop"].strip().lower(), row["sop"])
        row.update({"id": f"legacy{item.pk}", "ref": refs.get(tuple(row[key] for key in ("p", "l1", "l2", "l3", "l4"))),
                    "ctry": "All", "dir": "", "mgsc": "", "exc": "", "legacy_id": item.pk,
                    "legacy_fields": {field: getattr(item, field) for field in LEGACY_FIELDS}})
        tasks.append(row)
    return {"cat": None, "task": tasks, "seq": 1, "mode": "task" if tasks else ""}


def _validate_state(raw, project):
    if not isinstance(raw, dict) or raw.get("mode", "") not in ("", "cat", "task"):
        raise ValueError("Invalid scoping method.")
    state = copy.deepcopy(raw)
    if not isinstance(state.get("seq"), int) or isinstance(state["seq"], bool) or state["seq"] < 1:
        raise ValueError("Invalid task sequence.")
    catalogue = _catalogue()
    countries = set(project.countries or [])
    for method in ("cat", "task"):
        rows = state.get(method)
        if method == "cat" and rows is None:
            continue
        if not isinstance(rows, list) or len(rows) > 20000:
            raise ValueError("Invalid scope rows.")
        ids = set()
        refs = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", row["id"]) or row["id"] in ids:
                raise ValueError("Missing or duplicate row ID.")
            ids.add(row["id"])
            legacy = row.get("legacy_fields", {})
            if not isinstance(legacy, dict):
                raise ValueError("Invalid legacy task details.")
            for field in LEGACY_FIELDS:
                value = legacy.get(field, "")
                limit = OpportunityAssessment._meta.get_field(field).max_length
                if not isinstance(value, str) or (limit and len(value) > limit):
                    raise ValueError(f"Invalid legacy {field}.")
            ref = row.get("ref")
            if ref is not None:
                if not isinstance(ref, int) or isinstance(ref, bool) or ref < 0 or ref >= len(catalogue) or ref in refs:
                    raise ValueError("Invalid or duplicate catalogue reference.")
                refs.add(ref)
                item = catalogue[ref]
                row.update(dict(zip(("p", "l1", "l2", "l3", "l4", "dir", "mig"), item[:7])))
            elif not row.get("legacy_id"):
                raise ValueError("Task must reference the service catalogue.")
            for key, field in FIELD_MAP.items():
                value = row.get(key, "")
                if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                    raise ValueError(f"Invalid {field}.")
                row[key] = str(value).strip()
                max_length = OpportunityAssessment._meta.get_field(field).max_length
                if max_length and len(row[key]) > max_length:
                    raise ValueError(f"{field} exceeds {max_length} characters.")
            for key, choices in OPTIONS.items():
                if row.get(key, "") not in choices:
                    raise ValueError(f"Invalid {key} value.")
            country = row.get("ctry") or "All"
            if not isinstance(country, str) or (country != "All" and not set(country.split("; ")).issubset(countries)):
                raise ValueError("Country must belong to this project's intake.")
            row["ctry"] = country
            for key in ("vol", "tpu"):
                if row[key] and (_parse_number(row[key]) is None or _parse_number(row[key]) < 0):
                    raise ValueError("Volume and task time must be finite non-negative numbers.")
            volume, minutes = _parse_number(row["vol"]), _parse_number(row["tpu"])
            factor = FREQUENCIES.get(row["freq"])
            row["hrs"] = 140
            row["fte"] = f"{volume * minutes * factor / 60 / 140:.4f}" if volume and minutes and factor else ""
    if state.get("mode") == "cat" and state.get("cat") is None:
        raise ValueError("Catalogue data is missing.")
    return state


def _sync_rows(project, state, setup):
    existing = list(OpportunityAssessment.objects.filter(migration_request_id=project.migration_request_id))
    by_key = {(item.scope_details.get("method"), item.scope_details.get("row_id")): item for item in existing if item.scope_details}
    by_id = {item.pk: item for item in existing}
    keep = []
    updates = []
    creates = []
    mode = state.get("mode")
    for row in (state.get(mode) or []) if mode else []:
        item = by_key.get((mode, row["id"])) or by_id.get(row.get("legacy_id"))
        if item is None:
            item = OpportunityAssessment(migration_request_id=project.migration_request_id)
        for key, field in FIELD_MAP.items():
            setattr(item, field, row.get(key, ""))
        for field in LEGACY_FIELDS:
            if field in row.get("legacy_fields", {}):
                setattr(item, field, row["legacy_fields"][field])
        item.owner = setup["owner_default"]
        item.area = setup["default_area"]
        item.gsc_site = row.get("loc", "")
        item.fte_calculation = row.get("fte", "")
        item.task_found_in_service_catalog = "Y" if row.get("ref") is not None else "N"
        item.scope_details = {**row, "method": mode, "row_id": row["id"]}
        item.updated_at = timezone.now()
        if item.pk:
            keep.append(item.pk)
            updates.append(item)
        else:
            creates.append(item)
    OpportunityAssessment.objects.filter(migration_request_id=project.migration_request_id).exclude(pk__in=keep).delete()
    if updates:
        OpportunityAssessment.objects.bulk_update(updates, [*FIELD_MAP.values(), *LEGACY_FIELDS, "owner", "area", "gsc_site", "fte_calculation", "task_found_in_service_catalog", "scope_details", "updated_at"], batch_size=50)
    if creates:
        OpportunityAssessment.objects.bulk_create(creates, batch_size=50)


@api_view(["GET", "POST"])
def opportunity_task_scope(request, project_id):
    project = _get_project(project_id)
    if project is None:
        return Response({"error": "Project not found."}, status=404)
    denied = _deny_unless_requestor(request, project)
    if denied is not None:
        return denied
    setup = _build_setup_context(project)
    if request.method == "POST":
        if request.data.get("migration_request_id") != project.migration_request_id:
            return Response({"error": "migration_request_id does not match this project."}, status=400)
        try:
            state = _validate_state(request.data.get("state"), project)
        except (ValueError, TypeError) as error:
            return Response({"error": str(error)}, status=400)
        with transaction.atomic():
            MigrationIntakeSubmission.objects.select_for_update().get(pk=project.pk)
            scope, _created = OpportunityAssessmentScope.objects.get_or_create(project=project)
            if request.data.get("revision") != scope.revision:
                return Response({"error": "This assessment was changed by another user. Reload before saving."}, status=409)
            _sync_rows(project, state, setup)
            scope.state = state
            scope.revision += 1
            scope.updated_by = get_request_email(request)
            scope.save()
    else:
        scope = OpportunityAssessmentScope.objects.filter(project=project).first()
        state = scope.state if scope else _initial_state(project)
    registration = StakeholderRegistration.objects.filter(project=project).only(
        "team_members", "assignments"
    ).first()
    fpo_approvers = _assigned_role_emails(registration, "fpo")
    return Response({
        "migration_request_id": project.migration_request_id,
        "state": state, "revision": scope.revision if scope else 0,
        "fpo_approver_email": fpo_approvers[0] if len(fpo_approvers) == 1 else "",
        "catalogue_requests": catalogue_request_reminders(project),
        "catalogue_additions": _catalogue_additions(),
        "intake": {"region": project.region, "area": ", ".join(project.areas or []),
                   "product": ", ".join(project.products or []), "products": project.products or [],
                   "catalogue_products": [re.sub(r"^General\s+", "", product, flags=re.IGNORECASE).strip() for product in (project.products or [])],
                   "owner": setup["owner_default"], "countries": project.countries or []},
        "locations": list(dict.fromkeys([*setup["location_options"], "Manila", "Pune", "Mumbai", "Chengdu", "Ho Chi Minh City"])),
        "default_location": setup["location_options"][0] if setup["location_options"] else "Manila",
    })