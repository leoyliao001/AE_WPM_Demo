from api.models import MigrationIntakeSubmission


def _join_preview(values, limit=3):
    items = [str(value).strip() for value in (values or []) if str(value).strip()]
    if not items:
        return "—"
    preview = ", ".join(items[:limit])
    if len(items) > limit:
        preview += f" (+{len(items) - limit} more)"
    return preview


def _serialize_approval_file(submission):
    if not submission.custom_approval_file_name:
        return None
    return {
        "name": submission.custom_approval_file_name,
        "size": submission.custom_approval_file_size,
        "type": submission.custom_approval_file_type,
    }


def serialize_project_overview(submission: MigrationIntakeSubmission) -> dict:
    return {
        "id": submission.id,
        "migrationRequestId": submission.migration_request_id,
        "projectName": submission.project_name,
        "requestor": submission.requestor,
        "requestedDate": submission.requested_date,
        "status": submission.status,
        "region": submission.region,
        "migrationType": submission.migration_type,
        "migrationTypeValue": submission.migration_type_value,
        "function": submission.function_name,
        "fteNumber": submission.fte_number,
        "areasCount": len(submission.areas or []),
        "countriesCount": len(submission.countries or []),
        "productsPreview": _join_preview(submission.products),
        "products": submission.products or [],
        "areasPreview": _join_preview(submission.areas),
        "createdAt": submission.created_at.isoformat() if submission.created_at else "",
    }


def serialize_project_detail(submission: MigrationIntakeSubmission) -> dict:
    overview = serialize_project_overview(submission)
    overview.update(
        {
            "areas": submission.areas or [],
            "countries": submission.countries or [],
            "areaCountryPairs": submission.area_country_pairs or [],
            "defaultLocationStrategies": submission.default_location_strategies or [],
            "customLocationStrategies": submission.custom_location_strategies or [],
            "locationStrategyCustom": submission.location_strategy_custom,
            "customLocationStrategyJustification": submission.custom_location_strategy_justification,
            "customApprovalFile": _serialize_approval_file(submission),
            "products": submission.products or [],
            "proposedScope": submission.proposed_scope,
            "languageDependencies": submission.language_dependencies or [],
            "jl2": submission.jl2,
            "jl3": submission.jl3,
            "jl4": submission.jl4,
            "jobLevelTotal": submission.job_level_total,
            "risks": submission.risks,
            "updatedAt": submission.updated_at.isoformat() if submission.updated_at else "",
        }
    )
    return overview


def _parse_fte(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _add_bucket(bucket: dict, key: str, fte: int) -> None:
    if not key:
        return
    entry = bucket.get(key, {"count": 0, "fte": 0})
    entry["count"] += 1
    entry["fte"] += fte
    bucket[key] = entry


def build_dashboard_summary(submissions) -> dict:
    total_fte = 0
    by_status = {}
    by_region = {}
    by_product = {}

    for submission in submissions:
        fte = _parse_fte(submission.fte_number)
        total_fte += fte
        _add_bucket(by_status, submission.status, fte)
        _add_bucket(by_region, submission.region, fte)
        for product in submission.products or []:
            product_name = str(product).strip()
            if product_name:
                _add_bucket(by_product, product_name, fte)

    return {
        "totalProjects": len(submissions),
        "totalFte": total_fte,
        "byStatus": by_status,
        "byRegion": by_region,
        "byProduct": by_product,
    }
