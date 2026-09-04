from api.models import MigrationIntakeSubmission, OpportunityAssessment


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
    owner = ""
    try:
        owner = (
            OpportunityAssessment.objects.filter(migration_request_id=submission.migration_request_id)
            .values_list("owner", flat=True)
            .first()
            or ""
        )
    except Exception:
        owner = ""

    return {
        "id": submission.id,
        "migrationRequestId": submission.migration_request_id,
        "projectName": submission.project_name,
        "requestor": submission.requestor,
        "owner": owner,
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
            "businessCaseSubmissionDate": (
                submission.business_case_submission_date.isoformat()
                if submission.business_case_submission_date
                else ""
            ),
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

    result = {
        "totalProjects": len(submissions),
        "totalFte": total_fte,
        "byStatus": by_status,
        "byRegion": by_region,
        "byProduct": by_product,
    }

    # TG-level status summary (counts + fte per TG per RAG-like bucket)
    try:
        from api.models import ProjectGanttPlan
        from api.views import project_gantt as _pg
    except Exception:
        # If imports fail, return result without tg_summary
        return result

    # TG labels follow canonical template order
    TG_LABELS = [
        "TG1 - Assessment",
        "TG2 - Business Case",
        "TG3 - Mobilization",
        "TG4 - Training & KT",
        "TG5 - Ramp Up",
        "TG6 - Hypercare",
        "TG7 - Closure",
    ]

    # Initialize buckets
    tg_summary = []
    for label in TG_LABELS:
        tg_summary.append({
            "label": label,
            "Delayed": {"count": 0, "fte": 0},
            "Delayed < 30 Days": {"count": 0, "fte": 0},
            "On Time": {"count": 0, "fte": 0},
            "Update Pending": {"count": 0, "fte": 0},
        })

    def _parse_int(v):
        try:
            return int(v or 0)
        except Exception:
            return 0

    for submission in submissions:
        fte = _parse_int(submission.fte_number)
        # try load saved gantt tasks
        plan = ProjectGanttPlan.objects.filter(project=submission).first()
        tasks = plan.tasks if plan else None
        created_at = getattr(submission, "created_at", None)

        if not tasks or not isinstance(tasks, list):
            # No tasks saved -> whole-project considered Update Pending for all TGs
            for tg in tg_summary:
                tg["Update Pending"]["count"] += 1
                tg["Update Pending"]["fte"] += fte
            continue

        # Evaluate each task in saved order; map to TG_LABELS by index
        for idx in range(len(TG_LABELS)):
            if idx < len(tasks):
                task = tasks[idx] or {}
            else:
                task = {}

            plan_range = task.get("plan") or task.get("standard") or {}
            actual_range = task.get("actual")
            completed_at = task.get("completedAt") or task.get("completed_at")

            plan_end = None
            actual_end = None
            try:
                plan_end = int(plan_range.get("endWeek")) if plan_range and plan_range.get("endWeek") is not None else None
            except Exception:
                plan_end = None
            try:
                actual_end = int(actual_range.get("endWeek")) if actual_range and actual_range.get("endWeek") is not None else None
            except Exception:
                actual_end = None

            bucket = None
            # If we can compare weeks, use week-based delta (approx days = weeks*7)
            if plan_end is not None and actual_end is not None:
                delta_weeks = actual_end - plan_end
                if delta_weeks <= 0:
                    bucket = "On Time"
                else:
                    if delta_weeks * 7 < 30:
                        bucket = "Delayed < 30 Days"
                    else:
                        bucket = "Delayed"
            else:
                # Try to derive completed week from completed_at using project_gantt helper
                if completed_at:
                    try:
                        completed_week = _pg._week_index_for_date(created_at, completed_at)
                    except Exception:
                        completed_week = None
                    if plan_end is not None and completed_week is not None:
                        delta_weeks = completed_week - plan_end
                        if delta_weeks <= 0:
                            bucket = "On Time"
                        else:
                            if delta_weeks * 7 < 30:
                                bucket = "Delayed < 30 Days"
                            else:
                                bucket = "Delayed"
                    else:
                        # completed but no plan -> treat as On Time
                        bucket = "On Time"
                else:
                    # No actual/completed -> Update Pending
                    bucket = "Update Pending"

            tg_entry = tg_summary[idx]
            tg_entry[bucket]["count"] += 1
            tg_entry[bucket]["fte"] += fte

    result["tg_summary"] = tg_summary
    return result
