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
DEFAULT_CALENDAR_START_WEEK = 9

BAR_TYPES = ("standard", "plan", "actual")
BAR_TYPE_META = [
    {
        "id": "standard",
        "label": "Standard",
        "hint": "Standard cycle (fixed)",
        "color": "#8E9BA8",
    },
    {
        "id": "plan",
        "label": "Plan",
        "hint": "Editable plan",
        "color": "#1E8BB5",
    },
    {
        "id": "actual",
        "label": "Actual",
        "hint": "Auto from completion · green if within Plan, pink if beyond",
        "color": "#6DBF80",
        "lateColor": "#E57F90",
    },
]

META_TEXT_KEYS = ("projectPhase", "scope")
META_NUMBER_KEYS = (
    "migratableFte",
    "learningCurve",
    "tlTmHc",
    "mngrHc",
    "totalWoBuffer",
    "total",
)

# Fixed Migration Key Steps — Standard ranges match Excel template.
TEMPLATE_TASKS = [
    {"id": "business-case", "name": "Business Case (Memo)", "startWeek": 1, "endWeek": 5},
    {"id": "fbp-approval", "name": "FBP approval", "startWeek": 1, "endWeek": 5},
    {"id": "functional-head", "name": "Functional head approval", "startWeek": 3, "endWeek": 5},
    {"id": "elt-approval", "name": "ELT approg", "startWeek": 3, "endWeek": 5},
    {"id": "gsc-head", "name": "GSC Head -1 approval", "startWeek": 3, "endWeek": 5},
    {
        "id": "opportunity-assessment",
        "name": "Opportunity Assessment (Detailed task scoping)",
        "startWeek": 1,
        "endWeek": 5,
    },
    {"id": "pid-approval", "name": "PID Approval", "startWeek": 6, "endWeek": 12},
    {"id": "hiring-request", "name": "Hiring Request approval", "startWeek": 6, "endWeek": 12},
    {"id": "resource-mobilization", "name": "Resource mobilization", "startWeek": 13, "endWeek": 23},
    {
        "id": "neo-training",
        "name": "NEO + GSC L&D business & training stage",
        "startWeek": 24,
        "endWeek": 27,
    },
    {
        "id": "knowledge-transfer",
        "name": "Knowledge Transfer Business + System Training sessions + Assessments",
        "startWeek": 28,
        "endWeek": 30,
    },
    {"id": "volume-transfer", "name": "Volume Transfer/Ramp-up stage", "startWeek": 31, "endWeek": 36},
    {"id": "hypercare", "name": "Hypercare stage", "startWeek": 37, "endWeek": 41},
    {
        "id": "hypercare-exit",
        "name": "Hypercare Exit Success Criteria Review",
        "startWeek": 42,
        "endWeek": 42,
    },
    {"id": "sign-off", "name": "Migration Sign-off recommendation", "startWeek": 43, "endWeek": 43},
    {
        "id": "capacity-release",
        "name": "Recommended soonest Capacity Release",
        "startWeek": 44,
        "endWeek": 44,
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


def _range_dict(start: int, end: int) -> dict:
    start_i, end_i = _clamp_week_range(int(start), int(end))
    return {"startWeek": start_i, "endWeek": end_i}


def _parse_range(raw, fallback: dict | None = None) -> dict | None:
    """Parse {startWeek,endWeek} or legacy flat start/end. None if empty and no fallback."""
    if isinstance(raw, dict):
        start = raw.get("startWeek")
        end = raw.get("endWeek")
        if start in (None, "") and end in (None, ""):
            return dict(fallback) if fallback else None
        try:
            return _range_dict(int(start), int(end))
        except (TypeError, ValueError):
            return dict(fallback) if fallback else None
    return dict(fallback) if fallback else None


def _week_index_for_date(created_at, target) -> Optional[int]:
    """
    Map a calendar date to timeline week index (1..N).
    Dates outside the chart are clamped to the nearest week.
    """
    target_date = _as_local_date(target)
    if not target_date:
        return None
    weeks = build_gantt_weeks(created_at)
    if not weeks:
        return None
    local_date = _as_local_date(created_at)
    if local_date:
        year, week, _weekday = local_date.isocalendar()
        start_monday = date.fromisocalendar(year, week, 1) + timedelta(weeks=1)
    else:
        start_monday = date.fromisocalendar(date.today().year, DEFAULT_CALENDAR_START_WEEK, 1)

    delta_days = (target_date - start_monday).days
    index = delta_days // 7 + 1
    return max(MIN_WEEK, min(len(weeks), index))


def _actual_status(plan: dict | None, actual: dict | None) -> Optional[str]:
    """Return 'on_time' | 'late' | None for Actual bar coloring."""
    if not plan or not actual:
        return None
    try:
        if int(actual["endWeek"]) <= int(plan["endWeek"]):
            return "on_time"
        return "late"
    except (TypeError, ValueError, KeyError):
        return None


def _refresh_actual(
    plan: dict | None,
    saved_actual: dict | None,
    completed_at,
    created_at,
) -> dict | None:
    """
    Actual is driven by completion date when present:
    start = plan.startWeek (or completion week), end = completion week.
    Falls back to saved actual range.
    """
    completed_week = _week_index_for_date(created_at, completed_at)
    if completed_week is not None and plan:
        start = min(int(plan["startWeek"]), completed_week)
        return _range_dict(start, completed_week)
    return saved_actual


def build_template_tasks() -> list[dict]:
    """Return Standard baseline + default Plan (= Standard), Actual empty."""
    tasks = []
    for task in TEMPLATE_TASKS:
        standard = _range_dict(task["startWeek"], task["endWeek"])
        tasks.append(
            {
                "id": task["id"],
                "name": task["name"],
                "standard": standard,
                "plan": dict(standard),
                "actual": None,
                "completedAt": None,
                "actualStatus": None,
            }
        )
    return tasks


def merge_gantt_tasks_with_template(
    saved_tasks=None, created_at=None
) -> tuple[list[dict], list[dict]]:
    """
    Overlay saved Plan/Actual onto fixed Standard template by task id.
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
        standard = dict(base["standard"])

        # Legacy flat startWeek/endWeek → treat as Plan.
        if "plan" in saved or "standard" in saved or "actual" in saved:
            plan = _parse_range(saved.get("plan"), fallback=standard) or dict(standard)
            actual_raw = _parse_range(saved.get("actual"), fallback=None)
        else:
            plan = _parse_range(
                {"startWeek": saved.get("startWeek"), "endWeek": saved.get("endWeek")},
                fallback=standard,
            ) or dict(standard)
            actual_raw = None

        completed_at = saved.get("completedAt") or saved.get("completed_at") or None
        if completed_at == "":
            completed_at = None
        actual = _refresh_actual(plan, actual_raw, completed_at, created_at)

        merged.append(
            {
                "id": task_id,
                "name": base["name"],
                "standard": standard,
                "plan": plan,
                "actual": actual,
                "completedAt": completed_at,
                "actualStatus": _actual_status(plan, actual),
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

        # Plan is the editable range. Accept nested plan or legacy flat weeks.
        if isinstance(item.get("plan"), dict):
            plan = _parse_range(item.get("plan"))
        else:
            plan = _parse_range(
                {"startWeek": item.get("startWeek"), "endWeek": item.get("endWeek")}
            )
        if not plan:
            raise ValueError(f"Invalid plan week range for task {task_id}.")

        actual = _parse_range(item.get("actual"), fallback=None)
        completed_at = item.get("completedAt") or item.get("completed_at") or None
        if completed_at == "":
            completed_at = None
        if completed_at is not None:
            completed_at = str(completed_at).strip() or None

        normalized.append(
            {
                "id": task_id,
                "name": name,
                "plan": plan,
                "actual": actual,
                "completedAt": completed_at,
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
    saved_meta = (plan.meta if plan else {}) or {}
    saved_tasks = plan.tasks if plan else None
    tasks, template_tasks = merge_gantt_tasks_with_template(
        saved_tasks, created_at=project.created_at
    )
    weeks = build_gantt_weeks(project.created_at)
    start_week = weeks[0]["calendarWeekNumber"] if weeks else DEFAULT_CALENDAR_START_WEEK
    public_meta = {
        k: v for k, v in saved_meta.items() if k not in {"customPhases"}
    }
    return {
        "project_id": project.id,
        "migration_request_id": mid or None,
        "saved": bool(plan),
        "tasks": tasks,
        "template_tasks": template_tasks,
        "weeks": weeks,
        "calendar_start_week": start_week,
        "intake_created_at": project.created_at.isoformat() if project.created_at else None,
        "barTypes": BAR_TYPE_META,
        "meta": public_meta,
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
        existing = ProjectGanttPlan.objects.filter(project=project).first()
        # Drop obsolete customPhases from meta on save.
        if existing and isinstance(existing.meta, dict):
            preserved = {
                k: v
                for k, v in existing.meta.items()
                if k not in META_TEXT_KEYS
                and k not in META_NUMBER_KEYS
                and k != "customPhases"
            }
            preserved.update(meta)
            meta = preserved
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
