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
        "areasPreview": _join_preview(submission.areas),
        "createdAt": submission.created_at.isoformat() if submission.created_at else "",
    }


def serialize_project_detail(submission: MigrationIntakeSubmission) -> dict:
    overview = serialize_project_overview(submission)
    overview.update(
        {
            "areas": submission.areas or [],
            "countries": submission.countries or [],
            "locationStrategies": submission.location_strategies or [],
            "areaLocationPairs": submission.area_location_pairs or [],
            "areaCountryPairs": submission.area_country_pairs or [],
            "defaultSupportingGscSites": submission.default_supporting_gsc_sites or [],
            "customSupportingGscSites": submission.custom_supporting_gsc_sites or [],
            "supportingGscSitesCustom": submission.supporting_gsc_sites_custom,
            "customSupportingJustification": submission.custom_supporting_justification,
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


def build_dashboard_summary(submissions) -> dict:
    total_fte = 0
    by_status = {}
    by_region = {}

    for submission in submissions:
        by_status[submission.status] = by_status.get(submission.status, 0) + 1
        if submission.region:
            by_region[submission.region] = by_region.get(submission.region, 0) + 1
        try:
            total_fte += int(submission.fte_number or 0)
        except ValueError:
            pass

    return {
        "totalProjects": len(submissions),
        "totalFte": total_fte,
        "byStatus": by_status,
        "byRegion": by_region,
    }
