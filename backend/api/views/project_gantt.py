"""
Project Gantt API — per-project editable task week spans + summary meta.

Migration Key Steps rows are derived from Opportunity Assessment tasks for the
project's migration_request_id (not from a fixed Excel template). Saved plan
tasks are merged by id (`oa-<pk>`) to preserve week/phase edits.

GET  /api/migration-dashboard/projects/<id>/gantt/
PUT  /api/migration-dashboard/projects/<id>/gantt/
"""

from typing import Optional

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationIntakeSubmission, OpportunityAssessment, ProjectGanttPlan

MAX_WEEK = 44
MIN_WEEK = 1
DEFAULT_TASK_START = 1
DEFAULT_TASK_END = 5
DEFAULT_TASK_PHASE = "opportunity"

ALLOWED_PHASE_IDS = {
    "opportunity",
    "onboarding",
    "gss-training",
    "knowledge-transfer",
    "volume-rampup",
    "hypercare",
    "closure",
}

META_TEXT_KEYS = ("projectPhase", "scope")
META_NUMBER_KEYS = (
    "migratableFte",
    "learningCurve",
    "tlTmHc",
    "mngrHc",
    "totalWoBuffer",
    "total",
)


def _get_project(project_id: int):
    try:
        return MigrationIntakeSubmission.objects.get(pk=project_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return None


def _oa_display_name(row: OpportunityAssessment) -> str:
    name = (row.task_name or "").strip()
    if name:
        return name
    for candidate in (row.l4, row.l3, row.product):
        text = (candidate or "").strip()
        if text:
            return text
    return f"OA Task {row.id}"


def _clamp_week_range(start: int, end: int) -> tuple[int, int]:
    if start > end:
        start, end = end, start
    start = max(MIN_WEEK, min(MAX_WEEK, start))
    end = max(MIN_WEEK, min(MAX_WEEK, end))
    if start > end:
        start, end = end, start
    return start, end


def build_oa_baseline_tasks(migration_request_id: str) -> list[dict]:
    """One Gantt row per Opportunity Assessment task (defaults only)."""
    mid = (migration_request_id or "").strip()
    if not mid:
        return []

    tasks: list[dict] = []
    for row in OpportunityAssessment.objects.filter(migration_request_id=mid).order_by("id"):
        tasks.append(
            {
                "id": f"oa-{row.id}",
                "name": _oa_display_name(row),
                "startWeek": DEFAULT_TASK_START,
                "endWeek": DEFAULT_TASK_END,
                "phaseId": DEFAULT_TASK_PHASE,
                "opportunity_assessment_id": row.id,
            }
        )
    return tasks


def merge_gantt_tasks_with_oa(
    migration_request_id: str, saved_tasks=None
) -> tuple[list[dict], list[dict]]:
    """
    Build tasks from OA and overlay saved week/phase (and optional name) by id.
    Returns (merged_tasks, baseline_tasks).
    """
    baseline = build_oa_baseline_tasks(migration_request_id)
    saved_by_id: dict[str, dict] = {}
    if isinstance(saved_tasks, list):
        for item in saved_tasks:
            if isinstance(item, dict) and item.get("id"):
                saved_by_id[str(item["id"])] = item

    merged: list[dict] = []
    for base in baseline:
        task_id = base["id"]
        saved = saved_by_id.get(task_id) or {}
        start = saved.get("startWeek", base["startWeek"])
        end = saved.get("endWeek", base["endWeek"])
        try:
            start_i, end_i = _clamp_week_range(int(start), int(end))
        except (TypeError, ValueError):
            start_i, end_i = base["startWeek"], base["endWeek"]

        phase_id = str(saved.get("phaseId") or base["phaseId"] or DEFAULT_TASK_PHASE).strip()
        if phase_id not in ALLOWED_PHASE_IDS:
            phase_id = DEFAULT_TASK_PHASE

        name = str(saved.get("name") or "").strip() or base["name"]
        merged.append(
            {
                "id": task_id,
                "name": name,
                "startWeek": start_i,
                "endWeek": end_i,
                "phaseId": phase_id,
                "opportunity_assessment_id": base.get("opportunity_assessment_id"),
            }
        )
    return merged, baseline


def _normalize_tasks(raw_tasks):
    if not isinstance(raw_tasks, list):
        raise ValueError("tasks must be a list.")

    normalized = []
    seen = set()
    for item in raw_tasks:
        if not isinstance(item, dict):
            raise ValueError("Each task must be an object.")
        task_id = str(item.get("id") or "").strip()
        name = str(item.get("name") or "").strip()
        if not task_id:
            raise ValueError("Each task requires an id.")
        if task_id in seen:
            raise ValueError(f"Duplicate task id: {task_id}")
        seen.add(task_id)

        try:
            start = int(item.get("startWeek"))
            end = int(item.get("endWeek"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid week range for task {task_id}.") from exc

        if start > end:
            start, end = end, start
        if start < MIN_WEEK or end > MAX_WEEK:
            raise ValueError(
                f"Week range for task {task_id} must be between {MIN_WEEK} and {MAX_WEEK}."
            )

        phase_id = str(item.get("phaseId") or "").strip()
        if phase_id and phase_id not in ALLOWED_PHASE_IDS:
            raise ValueError(f"Invalid phaseId for task {task_id}: {phase_id}")

        normalized.append(
            {
                "id": task_id,
                "name": name,
                "startWeek": start,
                "endWeek": end,
                "phaseId": phase_id or "opportunity",
            }
        )
    return normalized


def _normalize_meta(raw_meta):
    if raw_meta is None:
        return {}
    if not isinstance(raw_meta, dict):
        raise ValueError("meta must be an object.")

    normalized = {}
    for key in META_TEXT_KEYS:
        if key not in raw_meta:
            continue
        normalized[key] = str(raw_meta.get(key) or "").strip()

    for key in META_NUMBER_KEYS:
        if key not in raw_meta:
            continue
        value = raw_meta.get(key)
        if value is None or value == "":
            normalized[key] = ""
            continue
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid number for meta.{key}.") from exc
        if number.is_integer():
            normalized[key] = int(number)
        else:
            normalized[key] = number

    return normalized


def _serialize_plan(
    plan: Optional[ProjectGanttPlan],
    project: MigrationIntakeSubmission,
) -> dict:
    mid = (project.migration_request_id or "").strip()
    saved_tasks = plan.tasks if plan else None
    tasks, oa_tasks = merge_gantt_tasks_with_oa(mid, saved_tasks)
    return {
        "project_id": project.id,
        "migration_request_id": mid or None,
        "saved": bool(plan),
        "tasks": tasks,
        "oa_tasks": oa_tasks,
        "oa_task_count": len(oa_tasks),
        "meta": (plan.meta if plan else {}) or {},
        "updated_at": plan.updated_at.isoformat() if plan and plan.updated_at else None,
    }


@api_view(["GET", "PUT"])
def project_gantt(request, project_id: int):
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        plan = ProjectGanttPlan.objects.filter(project=project).first()
        return Response(_serialize_plan(plan, project))

    try:
        tasks = _normalize_tasks(request.data.get("tasks"))
        meta = _normalize_meta(request.data.get("meta"))
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    plan, _created = ProjectGanttPlan.objects.update_or_create(
        project=project,
        defaults={
            "tasks": tasks,
            "meta": meta,
            "migration_request_id": project.migration_request_id or "",
        },
    )
    return Response(_serialize_plan(plan, project))
