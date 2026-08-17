"""
Opportunity Assessment API — task-level scoping grid per migration project.
"""

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from django.db.models import Q
from django.http import FileResponse

import re

from api.models import (
    FpoMapping,
    MigrationIntakeSubmission,
    OpportunityAssessment,
    ProductOwnership,
    ServiceCatalogue,
    WorkingHours,
)
from api.permissions.attributes_access import get_request_email, normalize_email
from api.services.opportunity_assessment_excel import (
    build_opportunity_template,
    parse_opportunity_workbook,
)
from api.views.fpo_mapping import _build_cascade_tree, _serialize_row as serialize_fpo_row

OA_REQUESTOR_DENIED = (
    "Access denied. This Opportunity Assessment was not submitted by you. "
    "Only the original requestor can open it."
)

# Labels for OA grid/API. Column order always follows OpportunityAssessment model field order.
OA_FIELD_LABELS = {
    "migration_request_id": "migration_request_id",
    "product": "Product",
    "owner": "Owner",
    "location": "Location",
    "l1": "L1",
    "l2": "L2",
    "l3": "L3",
    "l4": "L4",
    "task_name": "Task Name",
    "task_description": "Task Description",
    "upstream": "Upstream (tasks, events, input)",
    "downstream": "Downstream (task, events, output)",
    "risks_related": "Risks related to the Process/Task",
    "complexity": "Complexity (Low, Medium, High)",
    "sop_iop_exists": "SOP/IOP Exists?",
    "training_time_needed": "Training Time Needed",
    "recommended_handoff_duration": "Recommended Handoff Duration",
    "task_frequency": "Task Frequency",
    "unit_of_measure": "Unit of measure",
    "volume_monthly": "Volume Monthly",
    "task_time_per_unit_min": "Task time per unit (min)",
    "area": "Area",
    "gsc_site": "GSC Site",
    "task_found_in_service_catalog": "Task found in the corresponding Service Catalogue (Y/N)",
    "migratable_to_gsc": "Migratable to GSC as per service catalogue",
    "fte_calculation": "FTE Calculation",
}
OA_SKIP_FIELDS = frozenset({"id", "created_at", "updated_at"})


def _all_fields():
    """Return (key, label) pairs in OpportunityAssessment model definition order."""
    return [
        (field.name, OA_FIELD_LABELS.get(field.name, field.name))
        for field in OpportunityAssessment._meta.fields
        if field.name not in OA_SKIP_FIELDS
    ]


ALL_FIELDS = _all_fields()
WRITABLE_FIELDS = [key for key, _label in ALL_FIELDS if key != "migration_request_id"]
CASCADE_FIELD_KEYS = {"l1", "l2", "l3", "l4"}

# Working-hours lookup aliases (OA / intake names → Working Hours keys).
FTE_AREA_ALIASES = {
    "mekong": "mek",
    "oceania": "oce",
    "uki": "uki",
    "eaa": "eaf",
    "ecsa": "esa",
    "wcsa": "wsa",
    "caa": "can",
}
FTE_GSC_ALIASES = {
    "manila": "mnl",
    "mexico": "mex",
    "chengdu": "cdg",
    "chongqing": "cqg",
    "qingdao": "tao",
    "vietnam": "sgn",
    "mumbai": "bom",
    "chennai": "maa",
    "pune": "pnq",
    "poland": "poz",
    "brazil": "gru",
}


def _normalize_l3_key(value: str) -> str:
    return _normalize_value(value).casefold()


def _build_service_catalogue_l3_lookup() -> dict:
    """
    Map normalized L3 -> { found, ownership }.
    Ownership is unique Current Ownership values (first-seen order), joined by ', '.
    """
    lookup: dict = {}
    for row in ServiceCatalogue.objects.all().order_by("id").values("l3", "current_ownership"):
        l3 = _normalize_value(row.get("l3"))
        key = _normalize_l3_key(l3)
        if not key:
            continue
        entry = lookup.get(key)
        if not entry:
            entry = {"l3": l3, "found": True, "ownerships": []}
            lookup[key] = entry
        ownership = _normalize_value(row.get("current_ownership"))
        if ownership and ownership not in entry["ownerships"]:
            entry["ownerships"].append(ownership)

    for entry in lookup.values():
        entry["ownership"] = ", ".join(entry.pop("ownerships"))
    return lookup


def _apply_service_catalogue_link(payload: dict, lookup: dict) -> dict:
    """Fill task_found / migratable fields from Service Catalogue L3 match."""
    key = _normalize_l3_key(payload.get("l3", ""))
    if not key:
        payload["task_found_in_service_catalog"] = ""
        payload["migratable_to_gsc"] = ""
        return payload

    hit = lookup.get(key)
    if not hit:
        payload["task_found_in_service_catalog"] = "N"
        payload["migratable_to_gsc"] = ""
        return payload

    payload["task_found_in_service_catalog"] = "Y"
    payload["migratable_to_gsc"] = hit.get("ownership") or ""
    return payload


def _normalize_value(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _norm_hours_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _normalize_value(value).lower())


def _parse_number(value):
    text = _normalize_value(value).replace(",", "")
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if number != number or number in (float("inf"), float("-inf")):  # NaN / inf
        return None
    return number


def _format_fte(value: float) -> str:
    return f"{value:.4f}"


def _fte_hours_mode(project: MigrationIntakeSubmission) -> str:
    """area = 1:1 Transfer; gsc = New/Additional work."""
    value = _normalize_value(getattr(project, "migration_type_value", "")).lower()
    label = _normalize_value(getattr(project, "migration_type", "")).lower()
    if value in {"1:1-transfer", "1:1_transfer"} or "1:1 transfer" in label:
        return "area"
    if value in {"new-additional", "new_additional"} or "new/additional" in label or "additional work" in label:
        return "gsc"
    return ""


def _build_working_hours_lookup() -> dict:
    area_hours: dict[str, float] = {}
    gsc_hours: dict[str, float] = {}
    area_options: list[str] = []
    gsc_options: list[str] = []

    for item in WorkingHours.objects.all().order_by("id"):
        area = _normalize_value(item.area)
        area_val = _parse_number(item.aera_working_hours)
        if area and area_val and area_val > 0:
            key = _norm_hours_key(area)
            canon = FTE_AREA_ALIASES.get(key, key)
            if canon not in area_hours:
                area_hours[canon] = area_val
            if key not in area_hours:
                area_hours[key] = area_val
            if area not in area_options:
                area_options.append(area)

        gsc = _normalize_value(item.gsc)
        gsc_val = _parse_number(item.gsc_working_hours)
        if gsc and gsc_val and gsc_val > 0:
            key = _norm_hours_key(gsc)
            canon = FTE_GSC_ALIASES.get(key, key)
            if canon not in gsc_hours:
                gsc_hours[canon] = gsc_val
            if key not in gsc_hours:
                gsc_hours[key] = gsc_val
            if gsc not in gsc_options:
                gsc_options.append(gsc)

    for alias, canon in FTE_AREA_ALIASES.items():
        if canon in area_hours:
            area_hours.setdefault(alias, area_hours[canon])
    for alias, canon in FTE_GSC_ALIASES.items():
        if canon in gsc_hours:
            gsc_hours.setdefault(alias, gsc_hours[canon])

    return {
        "area": area_hours,
        "gsc": gsc_hours,
        "area_options": area_options,
        "gsc_options": gsc_options,
    }


def _lookup_working_hours(hours_map: dict, *candidates) -> float | None:
    for raw in candidates:
        key = _norm_hours_key(raw)
        if not key:
            continue
        if key in hours_map:
            return hours_map[key]
        canon_area = FTE_AREA_ALIASES.get(key)
        if canon_area and canon_area in hours_map:
            return hours_map[canon_area]
        canon_gsc = FTE_GSC_ALIASES.get(key)
        if canon_gsc and canon_gsc in hours_map:
            return hours_map[canon_gsc]
    return None


def _calculate_fte_value(volume_monthly, task_time_per_unit, working_hours) -> str:
    volume = _parse_number(volume_monthly)
    task_time = _parse_number(task_time_per_unit)
    hours = _parse_number(working_hours) if not isinstance(working_hours, (int, float)) else float(working_hours)
    if volume is None or task_time is None or hours is None or hours <= 0:
        return ""
    return _format_fte(((volume * 12) * task_time) / hours)


def _apply_fte_calculation(payload: dict, mode: str, lookup: dict, defaults: dict | None = None) -> dict:
    defaults = defaults or {}
    hours = None
    if mode == "area":
        hours = _lookup_working_hours(
            lookup.get("area") or {},
            payload.get("area"),
            defaults.get("area"),
        )
    elif mode == "gsc":
        hours = _lookup_working_hours(
            lookup.get("gsc") or {},
            payload.get("gsc_site"),
            payload.get("location"),
            defaults.get("gsc_site"),
        )
    payload["fte_calculation"] = _calculate_fte_value(
        payload.get("volume_monthly"),
        payload.get("task_time_per_unit_min"),
        hours,
    )
    return payload


def _build_fte_context(project: MigrationIntakeSubmission, setup: dict | None = None) -> dict:
    setup = setup or {}
    lookup = _build_working_hours_lookup()
    areas = setup.get("areas") or []
    locations = setup.get("location_options") or []
    mode = _fte_hours_mode(project)
    return {
        "mode": mode,
        "migration_type": project.migration_type or "",
        "migration_type_value": project.migration_type_value or "",
        "area_hours": {key: str(val) for key, val in lookup["area"].items()},
        "gsc_hours": {key: str(val) for key, val in lookup["gsc"].items()},
        "area_options": lookup["area_options"],
        "gsc_options": lookup["gsc_options"],
        "default_area": areas[0] if len(areas) == 1 else "",
        "default_gsc_site": locations[0] if len(locations) == 1 else "",
    }


def _build_setup_context(project: MigrationIntakeSubmission) -> dict:
    """Prefill defaults for OA row generation from intake + Product Ownership."""
    products = [str(p).strip() for p in (project.products or []) if str(p).strip()]
    areas = [str(a).strip() for a in (project.areas or []) if str(a).strip()]
    if project.location_strategy_custom:
        locations = [
            str(item).strip()
            for item in (project.custom_location_strategies or [])
            if str(item).strip()
        ]
    else:
        locations = [
            str(item).strip()
            for item in (project.default_location_strategies or [])
            if str(item).strip()
        ]

    region = (project.region or "").strip()
    ownership_qs = ProductOwnership.objects.filter(region=region)
    if areas:
        ownership_qs = ownership_qs.filter(Q(area__in=areas) | Q(area=""))

    owner_options: list[str] = []
    matched_rows: list[dict] = []
    matched_areas: list[str] = []
    for item in ownership_qs.order_by("id"):
        manager = (item.migration_manager or "").strip()
        area = (item.area or "").strip()
        matched_rows.append(
            {
                "region": item.region,
                "area": area,
                "migration_manager": manager,
            }
        )
        if area and area not in matched_areas:
            matched_areas.append(area)
        if manager and manager not in owner_options:
            owner_options.append(manager)

    return {
        "migration_request_id": project.migration_request_id,
        "project_name": project.project_name,
        "region": region,
        "areas": areas,
        "products": products,
        "products_display": ", ".join(products),
        "location_default": ", ".join(locations),
        "location_options": locations,
        "owner_default": owner_options[0] if owner_options else "",
        "owner_options": owner_options,
        "matched_ownership_areas": matched_areas,
        "matched_ownership_rows": matched_rows,
        "migration_type": project.migration_type or "",
        "migration_type_value": project.migration_type_value or "",
        "default_area": areas[0] if len(areas) == 1 else "",
        "default_gsc_site": locations[0] if len(locations) == 1 else "",
    }


def _serialize_row(item: OpportunityAssessment) -> dict:
    row = {"id": item.id}
    for key, _label in _all_fields():
        row[key] = getattr(item, key, "") or ""
    return row


def _get_project(project_id: int):
    try:
        return MigrationIntakeSubmission.objects.get(pk=project_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return None


def _deny_unless_requestor(request, project):
    """Only the intake requestor (SSO email) may access Opportunity Assessment."""
    email = get_request_email(request)
    if not email:
        return Response(
            {"error": "Sign in required. Missing SSO email."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if normalize_email(email) != normalize_email(project.requestor):
        return Response({"error": OA_REQUESTOR_DENIED}, status=status.HTTP_403_FORBIDDEN)
    return None


def _build_l1_l4_cascade() -> dict:
    """Build L1→L4 cascade options from FPO mapping dictionary."""
    qs = FpoMapping.objects.all().order_by("id")
    rows = [serialize_fpo_row(item) for item in qs]
    return _build_cascade_tree(rows)


def _is_new_record(record_id) -> bool:
    return record_id is None or record_id == "" or record_id is False


@api_view(["GET"])
def list_opportunity_assessment(request, project_id: int):
    """GET — rows for this project + L1→L4 cascade from FPO mapping."""
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    denied = _deny_unless_requestor(request, project)
    if denied:
        return denied

    migration_request_id = project.migration_request_id
    qs = OpportunityAssessment.objects.filter(
        migration_request_id=migration_request_id
    ).order_by("id")
    rows = [_serialize_row(item) for item in qs]
    sc_lookup = _build_service_catalogue_l3_lookup()
    setup = _build_setup_context(project)
    fte = _build_fte_context(project, setup)

    return Response(
        {
            "project_id": project.id,
            "migration_request_id": migration_request_id,
            "project_name": project.project_name,
            "count": len(rows),
            "has_existing_rows": len(rows) > 0,
            "setup": setup,
            "fte": fte,
            "columns": [{"key": key, "label": label} for key, label in _all_fields()],
            "cascade_keys": sorted(CASCADE_FIELD_KEYS),
            "cascade": _build_l1_l4_cascade(),
            "service_catalogue_by_l3": sc_lookup,
            "rows": rows,
        }
    )


@api_view(["POST"])
def save_opportunity_assessment(request, project_id: int):
    """POST — upsert rows; migration_request_id is always locked to the project."""
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    denied = _deny_unless_requestor(request, project)
    if denied:
        return denied

    unique_data = request.data.get("uniqueData")
    if not isinstance(unique_data, list) or len(unique_data) == 0:
        return Response(
            {"error": "uniqueData must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    migration_request_id = project.migration_request_id
    created_ids: list[int] = []
    updated_ids: list[int] = []
    errors: list[dict] = []
    sc_lookup = _build_service_catalogue_l3_lookup()
    setup = _build_setup_context(project)
    fte = _build_fte_context(project, setup)
    hours_lookup = {
        "area": {key: float(val) for key, val in fte["area_hours"].items()},
        "gsc": {key: float(val) for key, val in fte["gsc_hours"].items()},
    }
    fte_defaults = {
        "area": fte.get("default_area") or "",
        "gsc_site": fte.get("default_gsc_site") or "",
    }

    for index, item in enumerate(unique_data):
        if not isinstance(item, dict):
            errors.append({"index": index, "error": "Row must be an object."})
            continue

        record_id = item.get("id")
        payload = {
            field: _normalize_value(item.get(field))
            for field, _label in _all_fields()
            if field != "migration_request_id"
        }
        payload["migration_request_id"] = migration_request_id
        payload = _apply_service_catalogue_link(payload, sc_lookup)
        payload = _apply_fte_calculation(payload, fte["mode"], hours_lookup, fte_defaults)

        try:
            if _is_new_record(record_id):
                obj = OpportunityAssessment.objects.create(**payload)
                created_ids.append(obj.id)
            else:
                obj = OpportunityAssessment.objects.get(
                    pk=int(record_id),
                    migration_request_id=migration_request_id,
                )
                for field, value in payload.items():
                    setattr(obj, field, value)
                obj.save()
                updated_ids.append(obj.id)
        except OpportunityAssessment.DoesNotExist:
            errors.append({"id": record_id, "error": "Record not found for this project."})
        except (TypeError, ValueError) as exc:
            errors.append({"id": record_id, "error": f"Invalid id: {exc}"})
        except Exception as exc:  # noqa: BLE001
            errors.append({"id": record_id, "error": str(exc)})

    success_count = len(created_ids) + len(updated_ids)
    result_status = "success" if not errors else ("partial_success" if success_count else "error")
    http_status = status.HTTP_200_OK if success_count else status.HTTP_400_BAD_REQUEST

    return Response(
        {
            "status": result_status,
            "migration_request_id": migration_request_id,
            "success_count": success_count,
            "created_count": len(created_ids),
            "updated_count": len(updated_ids),
            "created_ids": created_ids,
            "updated_ids": updated_ids,
            "error_count": len(errors),
            "errors": errors,
        },
        status=http_status,
    )


@api_view(["DELETE"])
def delete_opportunity_assessment(request, project_id: int):
    """DELETE — remove rows belonging to this project's migration_request_id."""
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    denied = _deny_unless_requestor(request, project)
    if denied:
        return denied

    removed_ids = request.data.get("removedIds")
    if not isinstance(removed_ids, list) or len(removed_ids) == 0:
        return Response(
            {"error": "removedIds must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    migration_request_id = project.migration_request_id
    deleted_count = 0
    errors: list[dict] = []

    for raw_id in removed_ids:
        try:
            pk = int(raw_id)
            deleted, _ = OpportunityAssessment.objects.filter(
                pk=pk,
                migration_request_id=migration_request_id,
            ).delete()
            if deleted:
                deleted_count += deleted
            else:
                errors.append({"id": raw_id, "error": "Record not found for this project."})
        except (TypeError, ValueError) as exc:
            errors.append({"id": raw_id, "error": f"Invalid id: {exc}"})
        except Exception as exc:  # noqa: BLE001
            errors.append({"id": raw_id, "error": str(exc)})

    return Response(
        {
            "status": True,
            "deleted_count": deleted_count,
            "error_count": len(errors),
            "errors": errors,
        }
    )


@api_view(["GET"])
def download_opportunity_template(request, project_id: int):
    """
    Download Excel template with:
    - migration_request_id pre-filled for 200 rows
    - L1→L2→L3→L4 cascading dropdowns from fpo_mapping
    """
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    denied = _deny_unless_requestor(request, project)
    if denied:
        return denied

    try:
        buffer = build_opportunity_template(project.migration_request_id)
    except FileNotFoundError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as exc:  # noqa: BLE001
        return Response(
            {"error": f"Failed to build template: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    filename = f"Opportunity_Assessment_{project.migration_request_id}.xlsx"
    response = FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["X-Migration-Request-Id"] = project.migration_request_id
    return response


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_opportunity_excel(request, project_id: int):
    """
    Bulk upload a filled Opportunity Assessment Excel file.
    Every non-empty row must have migration_request_id matching this project.
    """
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    denied = _deny_unless_requestor(request, project)
    if denied:
        return denied

    upload = request.FILES.get("file")
    if not upload:
        return Response(
            {"error": "Please upload an Excel file (.xlsx)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    name = (upload.name or "").lower()
    if not name.endswith((".xlsx", ".xlsm")):
        return Response(
            {"error": "Only .xlsx Excel files are supported."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    migration_request_id = project.migration_request_id

    try:
        parsed = parse_opportunity_workbook(upload, migration_request_id)
    except Exception as exc:  # noqa: BLE001
        return Response(
            {"error": f"Failed to read Excel: {exc}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rows = parsed["rows"]
    row_errors = parsed["errors"]

    if not rows and row_errors:
        return Response(
            {
                "status": "error",
                "migration_request_id": migration_request_id,
                "error": (
                    "No rows imported. All filled rows failed migration_request_id validation. "
                    f"Expected: {migration_request_id}"
                ),
                "imported_count": 0,
                "rejected_count": len(row_errors),
                "errors": row_errors[:50],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not rows:
        return Response(
            {
                "status": "error",
                "migration_request_id": migration_request_id,
                "error": "No data rows found in the Excel file.",
                "imported_count": 0,
                "rejected_count": 0,
                "errors": [],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    objs = []
    sc_lookup = _build_service_catalogue_l3_lookup()
    setup = _build_setup_context(project)
    fte = _build_fte_context(project, setup)
    hours_lookup = {
        "area": {key: float(val) for key, val in fte["area_hours"].items()},
        "gsc": {key: float(val) for key, val in fte["gsc_hours"].items()},
    }
    fte_defaults = {
        "area": fte.get("default_area") or "",
        "gsc_site": fte.get("default_gsc_site") or "",
    }
    for row in rows:
        payload = _apply_service_catalogue_link(dict(row), sc_lookup)
        payload = _apply_fte_calculation(payload, fte["mode"], hours_lookup, fte_defaults)
        objs.append(OpportunityAssessment(**payload))
    created = OpportunityAssessment.objects.bulk_create(objs, batch_size=200)

    return Response(
        {
            "status": "partial_success" if row_errors else "success",
            "migration_request_id": migration_request_id,
            "imported_count": len(created),
            "rejected_count": len(row_errors),
            "errors": row_errors[:50],
            "message": (
                f"Imported {len(created)} row(s) for {migration_request_id}."
                + (
                    f" Rejected {len(row_errors)} row(s) due to migration_request_id mismatch."
                    if row_errors
                    else ""
                )
            ),
        }
    )
