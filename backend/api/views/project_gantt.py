"""
Project Gantt API — per-project editable task week spans + summary meta.

Migration Key Steps are a fixed template (Excel / Project Gantt sheet). Saved
plan tasks are merged by id to preserve week/phase edits.

GET  /api/migration-dashboard/projects/<id>/gantt/
PUT  /api/migration-dashboard/projects/<id>/gantt/
"""

from typing import Optional
from datetime import date, datetime, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationIntakeSubmission, ProjectGanttPlan

MAX_WEEK = 44
MIN_WEEK = 1
TIMELINE_WEEK_COUNT = 44
DEFAULT_TASK_PHASE = "opportunity"
DEFAULT_CALENDAR_START_WEEK = 9

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

# Fixed Migration Key Steps (matches Excel / fixture attachment).
TEMPLATE_TASKS = [
    {
        "id": "business-case",
        "name": "Business Case (Memo)",
        "startWeek": 1,
        "endWeek": 5,
        "phaseId": "opportunity",
    },
    {
        "id": "fbp-approval",
        "name": "FBP approval",
        "startWeek": 1,
        "endWeek": 5,
        "phaseId": "opportunity",
    },
    {
        "id": "functional-head",
        "name": "Functional head approval",
        "startWeek": 3,
        "endWeek": 5,
        "phaseId": "opportunity",
    },
    {
        "id": "elt-approval",
        "name": "ELT approg",
        "startWeek": 3,
        "endWeek": 5,
        "phaseId": "opportunity",
    },
    {
        "id": "gsc-head",
        "name": "GSC Head -1 approval",
        "startWeek": 3,
        "endWeek": 5,
        "phaseId": "opportunity",
    },
    {
        "id": "opportunity-assessment",
        "name": "Opportunity Assessment (Detailed task scoping)",
        "startWeek": 1,
        "endWeek": 5,
        "phaseId": "opportunity",
    },
    {
        "id": "pid-approval",
        "name": "PID Approval",
        "startWeek": 6,
        "endWeek": 12,
        "phaseId": "onboarding",
    },
    {
        "id": "hiring-request",
        "name": "Hiring Request approval",
        "startWeek": 6,
        "endWeek": 12,
        "phaseId": "onboarding",
    },
    {
        "id": "resource-mobilization",
        "name": "Resource mobilization",
        "startWeek": 13,
        "endWeek": 23,
        "phaseId": "onboarding",
    },
    {
        "id": "neo-training",
        "name": "NEO + GSC L&D business & training stage",
        "startWeek": 24,
        "endWeek": 27,
        "phaseId": "gss-training",
    },
    {
        "id": "knowledge-transfer",
        "name": "Knowledge Transfer Business + System Training sessions + Assessments",
        "startWeek": 28,
        "endWeek": 30,
        "phaseId": "knowledge-transfer",
    },
    {
        "id": "volume-transfer",
        "name": "Volume Transfer/Ramp-up stage",
        "startWeek": 31,
        "endWeek": 36,
        "phaseId": "volume-rampup",
    },
    {
        "id": "hypercare",
        "name": "Hypercare stage",
        "startWeek": 37,
        "endWeek": 41,
        "phaseId": "hypercare",
    },
    {
        "id": "hypercare-exit",
        "name": "Hypercare Exit Success Criteria Review",
        "startWeek": 42,
        "endWeek": 42,
        "phaseId": "closure",
    },
    {
        "id": "sign-off",
        "name": "Migration Sign-off recommendation",
        "startWeek": 43,
        "endWeek": 43,
        "phaseId": "closure",
    },
    {
        "id": "capacity-release",
        "name": "Recommended soonest Capacity Release",
        "startWeek": 44,
        "endWeek": 44,
        "phaseId": "closure",
    },
]

def _get_project(project_id: int):
    try:
        return MigrationIntakeSubmission.objects.get(pk=project_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return None


def _as_local_date(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            return timezone.localtime(value).date()
        return value.date()
    if isinstance(value, date):
        return value
    return None


def calendar_start_week_from_intake(created_at) -> int:
    """
    Calendar weeks start at (ISO work week of intake submission) + 1.
    Wraps correctly across year boundaries (including 53-week years).
    """
    local_date = _as_local_date(created_at)
    if not local_date:
        return DEFAULT_CALENDAR_START_WEEK

    year, week, _weekday = local_date.isocalendar()
    start_monday = date.fromisocalendar(year, week, 1) + timedelta(weeks=1)
    return start_monday.isocalendar()[1]


def build_gantt_weeks(created_at=None, count: int = TIMELINE_WEEK_COUNT) -> list[dict]:
    """
    Build timeline + calendar week columns for the Gantt header.
    Calendar labels start at intake work-week + 1.
    """
    local_date = _as_local_date(created_at)
    if local_date:
        year, week, _weekday = local_date.isocalendar()
        start_monday = date.fromisocalendar(year, week, 1) + timedelta(weeks=1)
    else:
        # Fallback aligned to legacy Excel demo (Wk9 …).
        start_monday = date.fromisocalendar(date.today().year, DEFAULT_CALENDAR_START_WEEK, 1)

    weeks: list[dict] = []
    for index in range(count):
        day = start_monday + timedelta(weeks=index)
        _iy, iso_week, _id = day.isocalendar()
        weeks.append(
            {
                "index": index + 1,
                "timelineWeek": f"wk{index + 1:02d}",
                "calendarWeek": f"Wk{iso_week}",
                "calendarWeekNumber": iso_week,
                "calendarYear": day.isocalendar()[0],
            }
        )
    return weeks


def _clamp_week_range(start: int, end: int) -> tuple[int, int]:
    if start > end:
        start, end = end, start
    start = max(MIN_WEEK, min(MAX_WEEK, start))
    end = max(MIN_WEEK, min(MAX_WEEK, end))
    if start > end:
        start, end = end, start
    return start, end


def build_template_tasks() -> list[dict]:
    """Return a copy of the fixed Migration Key Steps."""
    return [
        {
            "id": task["id"],
            "name": task["name"],
            "startWeek": task["startWeek"],
            "endWeek": task["endWeek"],
            "phaseId": task["phaseId"],
        }
        for task in TEMPLATE_TASKS
    ]


def merge_gantt_tasks_with_template(saved_tasks=None) -> tuple[list[dict], list[dict]]:
    """
    Overlay saved week/phase onto the fixed template by task id.
    Returns (merged_tasks, baseline_tasks).
    """
    baseline = build_template_tasks()
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
            phase_id = base["phaseId"]

        merged.append(
            {
                "id": task_id,
                "name": base["name"],
                "startWeek": start_i,
                "endWeek": end_i,
                "phaseId": phase_id,
            }
        )
    return merged, baseline


# Backwards-compatible alias for older imports.
def merge_gantt_tasks_with_oa(migration_request_id: str, saved_tasks=None):
    return merge_gantt_tasks_with_template(saved_tasks)


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
    tasks, template_tasks = merge_gantt_tasks_with_template(saved_tasks)
    weeks = build_gantt_weeks(project.created_at)
    start_week = weeks[0]["calendarWeekNumber"] if weeks else DEFAULT_CALENDAR_START_WEEK
    return {
        "project_id": project.id,
        "migration_request_id": mid or None,
        "saved": bool(plan),
        "tasks": tasks,
        "template_tasks": template_tasks,
        "weeks": weeks,
        "calendar_start_week": start_week,
        "intake_created_at": project.created_at.isoformat() if project.created_at else None,
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
