import re
from copy import deepcopy
from datetime import date

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import ApprovalWorkflow, BusinessCase, BusinessCaseCostRate, MigrationIntakeSubmission
from api.permissions.approval_access import roles_for
from api.permissions.attributes_access import can_access_table, get_request_email, normalize_email, require_attributes_access
from api.services.business_case import (
    DETAIL_FIELDS, INTAKE_FIELDS, LEVELS, approval_progress, build_business_case,
    case_status, decimal_value, scope_ready,
)
from api.services.migration_dashboard import serialize_business_case_file
from api.services.intake_options import INTAKE_OPTIONS, validate_intake_selections


def _text(value, label, limit=10000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(f"{label} must be text of at most {limit} characters.")
    return value.strip()


def _permissions(project, email):
    owner = email == normalize_email(project.requestor)
    editor = owner or can_access_table(email, "business_case")
    return editor, editor or bool(roles_for(email, project.function_name, project.products)), owner


def _serialize(project, record, email):
    intake, scope, financials, fingerprint = build_business_case(project, record)
    progress = approval_progress(project)
    state = case_status(record, fingerprint, progress) if record else "draft"
    editor, _, owner = _permissions(project, email)
    return {
        "projectId": project.pk, "projectName": project.project_name, "migrationRequestId": project.migration_request_id,
        "saved": record is not None, "revision": record.revision if record else 0, "status": state,
        "canEdit": editor and state in {"draft", "returned"},
        "canSubmit": owner and state in {"draft", "returned"},
        "intake": intake, "intakeVersion": project.updated_at.isoformat(),
        "scope": scope, "details": {key: (record.details.get(key, "") if record else "") for key in DETAIL_FIELDS},
        "financialInputs": record.financial_inputs if record else {"oneTimeCost": "", "adjustment": "0", "adjustmentReason": ""},
        "financials": financials, "history": record.audit_log if record else [],
        "intakeHistory": project.intake_audit_log,
        "financialHistory": record.financial_history if record else [],
        "savedSnapshot": record.saved_snapshot if record else {},
        "sourceChanged": bool(record and record.source_fingerprint != fingerprint),
        "sourceVersion": fingerprint,
        "reviewRequired": state == "needs_review", "legacyFile": serialize_business_case_file(project),
        "submittedAt": record.submitted_at.isoformat() if record and record.submitted_at else None,
        "updatedAt": record.updated_at.isoformat() if record else None,
        "updatedBy": record.updated_by if record else "", "approval": progress,
    }


@api_view(["GET"])
def get_business_case(request, project_id):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required."}, status=401)
    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if not project:
        return Response({"error": "Project not found."}, status=404)
    if not _permissions(project, email)[1]:
        return Response({"error": "Only the requestor, Business Case maintainers and configured approvers may view this case."}, status=403)
    return Response(_serialize(project, BusinessCase.objects.filter(project=project).first(), email))


def _update_intake(project, values, email):
    if not isinstance(values, dict) or set(values) - set(INTAKE_FIELDS):
        raise ValueError("Intake must contain only editable Intake fields.")
    changes = {}
    list_fields = {"products", "countries", "areas", "default_location_strategies", "custom_location_strategies"}
    for key, raw in values.items():
        if key in list_fields:
            if not isinstance(raw, list) or len(raw) > 100:
                raise ValueError(f"{key} must be a list of at most 100 values.")
            value = [_text(item, key, 255) for item in raw]
            if any(not item for item in value) or len(set(value)) != len(value):
                raise ValueError(f"{key} values must be non-empty and unique.")
        elif key == "location_strategy_custom":
            if type(raw) is not bool:
                raise ValueError("location_strategy_custom must be true or false.")
            value = raw
        else:
            value = _text(raw, key, 10000 if key == "initial_rationale" else 255)
        if value != getattr(project, key):
            changes[key] = {"old": getattr(project, key), "new": value}
            setattr(project, key, value)
    for key in ("project_name", "migration_type", "function_name", "region"):
        if not getattr(project, key):
            raise ValueError(f"{key} cannot be empty.")
    for key in ("target_start_date", "target_end_date"):
        value = getattr(project, key)
        if value:
            try:
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError
            except ValueError:
                raise ValueError(f"{key} must be YYYY-MM-DD.")
    if project.target_start_date and project.target_end_date and project.target_end_date < project.target_start_date:
        raise ValueError("Target end date must not precede the start date.")
    validate_intake_selections(project, changes)
    derived = {}
    if "migration_type" in changes:
        derived["migration_type_value"] = next(
            item["value"] for item in INTAKE_OPTIONS["migrationTypes"] if item["label"] == project.migration_type
        )
    if {"areas", "countries"}.intersection(changes):
        derived["area_country_pairs"] = [
            {"area": area, "country": country}
            for area in sorted(project.areas)
            for country in sorted(project.countries)
            if country in INTAKE_OPTIONS["areaCountryMapping"].get(area, [])
        ]
    for key, value in derived.items():
        if value != getattr(project, key):
            changes[key] = {"old": getattr(project, key), "new": value}
            setattr(project, key, value)
    if changes:
        project.intake_audit_log = [*project.intake_audit_log, {
            "by": email, "at": timezone.now().isoformat(), "from": "business_case", "changes": changes,
        }]
        project.save()
    return changes


def _reset_workflow(project):
    from api.views.approval_cycle import ROLE_FIELD_MAP

    workflow, _ = ApprovalWorkflow.objects.get_or_create(migration_request_id=project.migration_request_id)
    for fields in ROLE_FIELD_MAP.values():
        for key, field in fields.items():
            setattr(workflow, field, None if key == "date" else "")
    workflow.bpm_budget_status = ""
    workflow.business_case_submitted_date = project.business_case_submission_date
    workflow.area_head_approval_trigger_date = None
    workflow.save()


@api_view(["POST"])
def save_business_case(request, project_id):
    payload = request.data
    if not isinstance(payload, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required."}, status=401)
    try:
        with transaction.atomic():
            project = MigrationIntakeSubmission.objects.select_for_update().filter(pk=project_id).first()
            if not project:
                return Response({"error": "Project not found."}, status=404)
            editor, _, owner = _permissions(project, email)
            if not editor:
                return Response({"error": "Only the requestor or a Business Case maintainer can edit this record."}, status=403)
            record = BusinessCase.objects.select_for_update().filter(project=project).first()
            if type(payload.get("revision")) is not int or payload["revision"] != (record.revision if record else 0):
                return Response({"error": "This Business Case has changed. Reload before saving."}, status=409)
            if payload.get("intakeVersion") != project.updated_at.isoformat():
                return Response({"error": "The project source has changed. Reload before saving."}, status=409)
            action = payload.get("action", "save")
            if not isinstance(action, str) or action not in {"save", "refresh", "submit", "revise"}:
                raise ValueError("Unsupported Business Case action.")
            if action == "submit" and not owner:
                return Response({"error": "Only the project requestor can submit the Business Case."}, status=403)
            if not record:
                record = BusinessCase(project=project)
            before = {"details": record.details, "financialInputs": record.financial_inputs, "status": record.status}
            _, _, _, old_fingerprint = build_business_case(project, record)
            if payload.get("sourceVersion") != old_fingerprint:
                return Response({"error": "Scope or cost rates have changed. Reload and review current sources before saving."}, status=409)
            state = case_status(record, old_fingerprint, approval_progress(project))
            if action == "revise":
                reason = _text(payload.get("reason", ""), "Revision reason", 2000)
                if not reason:
                    raise ValueError("A reason is required to reopen a Business Case.")
                if state in {"draft", "returned"}:
                    raise ValueError("This record is already editable.")
                record.status = "returned"
                record.review_required = False
                workflow = ApprovalWorkflow.objects.filter(migration_request_id=project.migration_request_id).first()
                before["approval"] = {
                    field.name: str(getattr(workflow, field.name))
                    for field in workflow._meta.fields
                } if workflow else {}
                project.business_case_submission_date = None
                project.save(update_fields=["business_case_submission_date", "updated_at"])
                _reset_workflow(project)
                changes = {}
            else:
                if state not in {"draft", "returned"}:
                    return Response({"error": "Submitted or changed-source cases are locked. Reopen for revision first."}, status=409)
                reason = ""
                changes = _update_intake(project, payload["intake"], email) if "intake" in payload else {}
                details = payload.get("details", record.details)
                if not isinstance(details, dict) or set(details) - set(DETAIL_FIELDS):
                    raise ValueError("Business Case details contain unsupported fields.")
                record.details = {key: _text(details.get(key, ""), key) for key in DETAIL_FIELDS}
                inputs = payload.get("financialInputs", record.financial_inputs)
                if not isinstance(inputs, dict) or set(inputs) - {"oneTimeCost", "adjustment", "adjustmentReason"}:
                    raise ValueError("Invalid financial inputs.")
                baseline = inputs.get("oneTimeCost", "")
                baseline = "" if baseline in ("", None) else str(decimal_value(baseline, "One-time cost"))
                adjustment = decimal_value(inputs.get("adjustment", "0"), "Adjustment", signed=True)
                if (baseline and decimal_value(baseline, "One-time cost").as_tuple().exponent < -2) or adjustment.as_tuple().exponent < -2:
                    raise ValueError("One-time cost and adjustment support at most 2 decimal places.")
                adjustment_reason = _text(inputs.get("adjustmentReason", ""), "Adjustment reason", 2000)
                if adjustment and not adjustment_reason:
                    raise ValueError("An adjustment reason is required.")
                if baseline and decimal_value(baseline, "One-time cost") + adjustment < 0:
                    raise ValueError("Adjusted one-time cost cannot be negative.")
                record.financial_inputs = {"oneTimeCost": baseline, "adjustment": str(adjustment), "adjustmentReason": adjustment_reason}
            intake, scope, financials, fingerprint = build_business_case(project, record)
            if action == "submit":
                errors = list(financials["errors"])
                if not scope_ready(scope):
                    errors.append("Scope must be submitted with locked FTE.")
                if not all(record.details.get(key) for key in ("rationale", "expectedBenefits", "recommendation")):
                    errors.append("Rationale, expected benefits and recommendation are required.")
                if not project.business_owner:
                    errors.append("Business Owner is required in Intake.")
                if errors:
                    raise ValueError(" ".join(dict.fromkeys(errors)))
                record.status = "submitted"
                record.submitted_at = timezone.now()
                project.business_case_submission_date = record.submitted_at
                if project.status == "new":
                    project.status = "in_review"
                project.save(update_fields=["business_case_submission_date", "status", "updated_at"])
                workflow = ApprovalWorkflow.objects.filter(migration_request_id=project.migration_request_id).first()
                before["approval"] = {field.name: str(getattr(workflow, field.name)) for field in workflow._meta.fields} if workflow else {}
                _reset_workflow(project)
            record.revision += 1
            record.source_fingerprint = fingerprint
            record.updated_by = email
            at = timezone.now().isoformat()
            record.saved_snapshot = deepcopy({
                "schemaVersion": 1, "revision": record.revision, "savedAt": at,
                "savedBy": email, "action": action,
                "projectId": project.pk, "projectName": project.project_name,
                "migrationRequestId": project.migration_request_id,
                "status": record.status,
                "submittedAt": record.submitted_at.isoformat() if record.submitted_at else None,
                "intake": intake, "scope": scope, "details": record.details,
                "financialInputs": record.financial_inputs, "financials": financials,
                "sourceFingerprint": fingerprint,
                "intakeVersion": project.updated_at.isoformat(),
                "approval": approval_progress(project),
            })
            record.audit_log = [*record.audit_log, {
                "action": action, "revision": record.revision, "by": email, "at": at,
                "reason": reason, "old": before,
                "new": {"details": record.details, "financialInputs": record.financial_inputs, "status": record.status},
                "intakeChanges": changes,
            }]
            record.financial_history = [*record.financial_history, {
                "revision": record.revision, "at": at, "by": email, "action": action,
                "inputs": record.financial_inputs, "financials": financials,
                "sourceSnapshot": {"intake": intake, "scope": scope},
                "sourceFingerprint": fingerprint,
                "pageSnapshot": record.saved_snapshot,
            }]
            record.save()
            if action == "submit":
                from api.views.approval_cycle import _notify_next_approvers
                from api.permissions.approval_access import load_approval_input_rows
                transaction.on_commit(lambda: _notify_next_approvers(project, approval_progress(project), load_approval_input_rows(), "submit"))
        return Response(_serialize(project, record, email))
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)


@api_view(["GET"])
@require_attributes_access("business_case")
def list_business_cases(_request):
    return Response({"rows": [{
        "id": item.pk, "projectId": item.project_id, "projectName": item.project.project_name,
        "migrationRequestId": item.project.migration_request_id, "revision": item.revision,
        "status": case_status(item, build_business_case(item.project, item)[3], approval_progress(item.project)),
        "details": item.details, "financialInputs": item.financial_inputs,
        "updatedAt": item.updated_at.isoformat(), "updatedBy": item.updated_by,
    } for item in BusinessCase.objects.select_related("project").order_by("-updated_at")]})


@api_view(["POST"])
@require_attributes_access("business_case")
def delete_business_case(request, project_id):
    if not isinstance(request.data, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    with transaction.atomic():
        project = MigrationIntakeSubmission.objects.select_for_update().filter(pk=project_id).first()
        item = BusinessCase.objects.select_for_update().filter(project=project).first() if project else None
        if not item:
            return Response({"error": "Business Case not found."}, status=404)
        if type(request.data.get("revision")) is not int or request.data["revision"] != item.revision:
            return Response({"error": "Record changed. Reload before deleting."}, status=409)
        if item.status not in {"draft", "returned"}:
            return Response({"error": "Reopen the submitted case for revision before deleting."}, status=409)
        item.delete()
    return Response({"deleted": True})


def _rate_row(item):
    return {"id": item.pk, "location": item.location, "jobLevel": item.job_level,
            "annualCost": str(item.annual_cost), "currency": item.currency, "usdRate": str(item.usd_rate),
            "year": item.year, "version": item.version, "updatedAt": item.updated_at.isoformat(),
            "updatedBy": item.updated_by, "history": item.audit_log}


@api_view(["GET", "POST"])
@require_attributes_access("cost_rates")
def cost_rates(request):
    if request.method == "GET":
        return Response({"rows": [_rate_row(item) for item in BusinessCaseCostRate.objects.order_by("location", "year", "job_level")]})
    payload = request.data
    if not isinstance(payload, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    try:
        with transaction.atomic():
            rate_id = payload.get("id")
            if rate_id is not None and type(rate_id) is not int:
                raise ValueError("id must be an integer.")
            item = BusinessCaseCostRate.objects.select_for_update().filter(pk=rate_id).first() if rate_id else BusinessCaseCostRate()
            if not item:
                return Response({"error": "Rate not found."}, status=404)
            if item.pk and payload.get("updatedAt") != item.updated_at.isoformat():
                return Response({"error": "Rate changed. Reload before editing."}, status=409)
            old = _rate_row(item) if item.pk else None
            item.location = _text(payload.get("location"), "Location", 255)
            item.job_level = payload.get("jobLevel")
            item.year = payload.get("year")
            item.version = _text(payload.get("version"), "Rate version", 64)
            item.currency = _text(payload.get("currency"), "Currency", 3).upper()
            item.annual_cost = decimal_value(payload.get("annualCost"), "Annual cost")
            item.usd_rate = decimal_value(payload.get("usdRate"), "USD conversion rate")
            if not item.location or not item.version or item.job_level not in LEVELS:
                raise ValueError("Location, version and a valid job level are required.")
            if type(item.year) is not int or not 2000 <= item.year <= 2200:
                raise ValueError("Year must be an integer between 2000 and 2200.")
            if not re.fullmatch(r"[A-Z]{3}", item.currency) or item.usd_rate <= 0 or (item.currency == "USD" and item.usd_rate != 1):
                raise ValueError("Use a three-letter currency and a positive USD conversion rate (1 for USD).")
            if item.usd_rate >= 10 ** 10:
                raise ValueError("USD conversion rate must be less than 10000000000.")
            if item.annual_cost.as_tuple().exponent < -4 or item.usd_rate.as_tuple().exponent < -8:
                raise ValueError("Annual cost supports 4 decimal places; USD conversion supports 8.")
            duplicate = BusinessCaseCostRate.objects.filter(location__iexact=item.location, job_level=item.job_level, year=item.year).exclude(pk=item.pk)
            if duplicate.exists():
                raise ValueError("A rate already exists for this location, job level and year.")
            item.updated_by = normalize_email(get_request_email(request))
            if old:
                old.pop("history")
            item.audit_log = [*item.audit_log, {"by": item.updated_by, "at": timezone.now().isoformat(),
                                               "old": old, "new": {key: str(payload.get(key, "")) for key in (
                                                   "location", "jobLevel", "year", "annualCost", "currency", "usdRate", "version")}}]
            item.save()
        return Response(_rate_row(item))
    except (ValueError, IntegrityError) as exc:
        return Response({"error": str(exc)}, status=400)


@api_view(["DELETE"])
@require_attributes_access("cost_rates")
def delete_cost_rate(request, rate_id):
    if not isinstance(request.data, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    with transaction.atomic():
        item = BusinessCaseCostRate.objects.select_for_update().filter(pk=rate_id).first()
        if not item:
            return Response({"error": "Rate not found."}, status=404)
        if request.data.get("updatedAt") != item.updated_at.isoformat():
            return Response({"error": "Rate changed. Reload before deleting."}, status=409)
        item.delete()
    return Response({"deleted": True})
