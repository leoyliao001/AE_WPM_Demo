import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext

from api.models import ApprovalWorkflow, BusinessCase, BusinessCaseCostRate, ScopeStatement

INTAKE_FIELDS = (
    "project_name", "migration_type", "function_name", "products", "countries",
    "default_location_strategies", "custom_location_strategies", "location_strategy_custom",
    "business_owner", "target_start_date", "target_end_date", "initial_rationale", "region", "areas",
)
DETAIL_FIELDS = ("rationale", "expectedBenefits", "risks", "dependencies", "recommendation")
LEVELS = ("JL2", "JL3", "JL4")


def decimal_value(value, label, *, signed=False):
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite decimal.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} must be a finite decimal.")
    if not result.is_finite() or abs(result) > Decimal("9999999999999") or (not signed and result < 0):
        raise ValueError(f"{label} is outside the permitted range.")
    return result


def money(value):
    return str(value.quantize(Decimal("0.01")))


def source_data(project):
    statement = ScopeStatement.objects.filter(project=project).prefetch_related("lines").first()
    scope = {
        "scopeText": statement.scope_text if statement else "",
        "outOfScope": statement.out_of_scope if statement else "",
        "assumptions": statement.assumptions if statement else "",
        "waves": statement.waves if statement else [],
        "status": statement.status if statement else "missing",
        "reviewRequired": statement.review_required if statement else False,
        "revision": statement.revision if statement else 0,
        "finalProjectFte": statement.final_project_fte if statement else None,
        "auditLog": statement.audit_log if statement else [],
        "lines": [
            {"jobLevel": line.job_level, "finalFte": line.final_fte,
             "lockedAt": line.locked_at.isoformat() if line.locked_at else None}
            for line in (statement.lines.all() if statement else [])
        ],
    }
    intake = {field: getattr(project, field) for field in INTAKE_FIELDS}
    # Keep untouched historical source fingerprints stable until a manual value is saved.
    if statement and statement.migratable_fte is not None:
        scope["migratableFte"] = str(statement.migratable_fte)
        scope["migratableFteConfirmed"] = statement.migratable_fte_confirmed
    return intake, scope


def scope_ready(scope):
    return bool(
        scope["status"] == "submitted" and not scope.get("reviewRequired") and scope["scopeText"].strip()
        and scope["finalProjectFte"] is not None
        and {line["jobLevel"] for line in scope["lines"]} == set(LEVELS)
        and all(line["lockedAt"] and line["finalFte"] is not None for line in scope["lines"])
        and sum(line["finalFte"] for line in scope["lines"]) == scope["finalProjectFte"]
    )


def calculate_financials(intake, scope, inputs):
    with localcontext() as context:
        context.prec = 50
        return _calculate_financials(intake, scope, inputs)


def _calculate_financials(intake, scope, inputs):
    errors = []
    warnings = []
    countries = intake["countries"]
    sites = intake["custom_location_strategies"] if intake["location_strategy_custom"] else intake["default_location_strategies"]
    if len(countries) != 1 or len(sites) != 1:
        errors.append("Exactly one source country and one destination GSC site are required. Multi-location FTE allocation is not yet captured.")
    if not scope_ready(scope):
        errors.append("Submit Scope with all three job levels locked and a matching final FTE total.")
    try:
        year = date.fromisoformat(intake["target_start_date"]).year
        end = date.fromisoformat(intake["target_end_date"])
        if end < date.fromisoformat(intake["target_start_date"]):
            raise ValueError
    except (ValueError, TypeError):
        year = None
        errors.append("Valid target start and end dates are required; the start year selects cost rates.")
    rates = []
    rows = []
    current = Decimal(0)
    future = Decimal(0)
    if len(countries) == len(sites) == 1 and year and scope_ready(scope):
        for line in scope["lines"]:
            fte = line["finalFte"]
            if not fte:
                continue
            pair = []
            for location in (countries[0], sites[0]):
                rate = BusinessCaseCostRate.objects.filter(location__iexact=location, job_level=line["jobLevel"], year=year).first()
                if not rate:
                    errors.append(f"Missing {year} {line['jobLevel']} cost rate for {location}.")
                    pair.append(None)
                    continue
                rates.append({
                    "id": rate.id, "location": rate.location, "jobLevel": rate.job_level,
                    "annualCost": str(rate.annual_cost), "currency": rate.currency,
                    "usdRate": str(rate.usd_rate), "year": rate.year, "version": rate.version,
                })
                pair.append(rate.annual_cost * rate.usd_rate)
            if all(value is not None for value in pair):
                source_rate, destination_rate = pair
                current_cost, future_cost = source_rate * fte, destination_rate * fte
                current += current_cost
                future += future_cost
                rows.append({"jobLevel": line["jobLevel"], "fte": fte, "sourceRate": money(source_rate),
                             "destinationRate": money(destination_rate), "currentCost": money(current_cost),
                             "futureCost": money(future_cost)})
    metrics = {key: None for key in (
        "currentAnnualCost", "futureAnnualCost", "annualGrossBenefit", "benefitPercent",
        "netFirstYearBenefit", "recurringAnnualBenefit", "paybackMonths", "adjustedOneTimeCost",
    )}
    baseline = inputs.get("oneTimeCost", "")
    if baseline in ("", None):
        errors.append("Enter the one-time migration cost baseline, including zero when applicable.")
    else:
        one_time = decimal_value(baseline, "One-time cost")
        adjustment = decimal_value(inputs.get("adjustment", "0"), "Adjustment", signed=True)
        if one_time + adjustment < 0:
            errors.append("Adjusted one-time cost cannot be negative.")
        if not errors:
            gross = current - future
            adjusted = one_time + adjustment
            metrics.update({
                "currentAnnualCost": money(current), "futureAnnualCost": money(future),
                "annualGrossBenefit": money(gross), "benefitPercent": money(gross / current * 100) if current else None,
                "netFirstYearBenefit": money(gross - adjusted), "recurringAnnualBenefit": money(gross),
                "paybackMonths": money(adjusted * 12 / gross) if gross > 0 else None,
                "adjustedOneTimeCost": money(adjusted),
            })
            if current == 0:
                warnings.append("Benefit percentage is undefined because current annual cost is zero.")
            if gross <= 0:
                warnings.append("There is no positive annual benefit; a payback period cannot be calculated.")
    warnings.append("First-year benefit follows the specified full run-rate formula; it is not prorated by migration waves.")
    return {"ready": not errors, "errors": errors, "warnings": warnings, "currency": "USD",
            "metrics": metrics, "rows": rows, "rateBasis": rates}


def source_fingerprint(intake, scope, financials):
    basis = {"intake": intake, "scope": scope, "rates": financials["rateBasis"]}
    return hashlib.sha256(json.dumps(basis, sort_keys=True).encode()).hexdigest()


def build_business_case(project, record=None):
    intake, scope = source_data(project)
    inputs = record.financial_inputs if record else {}
    financials = calculate_financials(intake, scope, inputs)
    return intake, scope, financials, source_fingerprint(intake, scope, financials)


def approval_progress(project):
    from api.views.approval_cycle import _progress

    workflow = ApprovalWorkflow.objects.filter(migration_request_id=project.migration_request_id).first()
    return _progress(workflow) if workflow else None


def case_status(record, fingerprint, progress):
    if record.review_required or (record.status == "submitted" and record.source_fingerprint != fingerprint):
        return "needs_review"
    if record.status == "submitted" and progress and progress["step"] > progress["seqLen"] and progress["completed"]:
        return "approved"
    return record.status


def online_case_is_approved(project):
    record = BusinessCase.objects.filter(project=project).first()
    if not record:
        return None
    *_, fingerprint = build_business_case(project, record)
    return case_status(record, fingerprint, approval_progress(project)) == "approved"
