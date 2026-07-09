from django.db import transaction

from api.models import MigrationIntakeSubmission


def _as_list(value):
    return value if isinstance(value, list) else []


def _unique_strings(values):
    seen = set()
    result = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _normalize_pairs(pairs, keys):
    result = []
    seen = set()
    for pair in _as_list(pairs):
        if not isinstance(pair, dict):
            continue
        item = {key: str(pair.get(source, "")).strip() for key, source in keys.items()}
        if not all(item.values()):
            continue
        signature = tuple(item.values())
        if signature in seen:
            continue
        seen.add(signature)
        result.append(item)
    return result


@transaction.atomic
def create_submission_from_payload(payload: dict) -> MigrationIntakeSubmission:
    approval_file = payload.get("customApprovalFile") or {}

    return MigrationIntakeSubmission.objects.create(
        migration_request_id=payload["migrationRequestId"],
        requested_date=payload.get("requestedDate", ""),
        requestor=payload.get("requestor", ""),
        status=payload.get("status", "new"),
        project_name=payload.get("projectName", ""),
        migration_type=payload.get("migrationType", ""),
        migration_type_value=payload.get("migrationTypeValue", ""),
        region=payload.get("region", ""),
        areas=_unique_strings(_as_list(payload.get("areas"))),
        countries=_unique_strings(_as_list(payload.get("countries"))),
        area_country_pairs=_normalize_pairs(
            payload.get("areaCountryPairs"),
            {"area": "area", "country": "country"},
        ),
        default_location_strategies=_unique_strings(
            _as_list(payload.get("defaultLocationStrategies"))
        ),
        custom_location_strategies=_unique_strings(
            _as_list(payload.get("customLocationStrategies"))
        ),
        location_strategy_custom=bool(payload.get("locationStrategyCustom")),
        custom_location_strategy_justification=payload.get(
            "customLocationStrategyJustification", ""
        ),
        custom_approval_file_name=approval_file.get("name", ""),
        custom_approval_file_size=approval_file.get("size") or None,
        custom_approval_file_type=approval_file.get("type", ""),
        function_name=payload.get("function", ""),
        products=_unique_strings(_as_list(payload.get("products"))),
        proposed_scope=payload.get("proposedScope", ""),
        language_dependencies=_unique_strings(
            _as_list(payload.get("languageDependencies"))
        ),
        fte_number=str(payload.get("fteNumber", "")),
        jl2=str(payload.get("jl2", "0")),
        jl3=str(payload.get("jl3", "0")),
        jl4=str(payload.get("jl4", "0")),
        job_level_total=int(payload.get("jobLevelTotal") or 0),
        risks=payload.get("risks", ""),
    )
