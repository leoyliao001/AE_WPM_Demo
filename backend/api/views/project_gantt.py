"""
Project Gantt API — per-project lifecycle-grouped task week spans.

Default (unsaved) projects use the Migration Key Steps template.
Once saved, the task list (order, names, add/remove/duplicates) is authoritative.

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
# Append-only Plan change log per stage (kept in tasks JSON).
MAX_PLAN_COMMENTS_PER_TASK = 100

BAR_TYPE_META = [
    {
        "id": "plan",
        "label": "Plan",
        "hint": "Editable plan",
        "color": "#1E8BB5",
    },
    {
        "id": "actual",
        "label": "Actual",
        "hint": "Recorded progress · green if within Plan, pink if beyond",
        "color": "#6DBF80",
        "lateColor": "#E57F90",
    },
]

LIFECYCLE_STAGE_IDS = frozenset(
    {"initiate", "plan", "execute", "monitor_control", "close_realize_value"}
)
META_TEXT_KEYS = ()
META_NUMBER_KEYS = ("total",)
OBSOLETE_META_KEYS = frozenset(
    {
        "projectPhase",
        "scope",
        "migratableFte",
        "learningCurve",
        "tlTmHc",
        "mngrHc",
        "totalWoBuffer",
    }
)
DEFAULT_LIFECYCLE_STAGE_BY_TASK_ID = {
    "business-case": "initiate",
    "fbp-approval": "initiate",
    "functional-head": "initiate",
    "elt-approval": "initiate",
    "gsc-head": "initiate",
    "opportunity-assessment": "initiate",
    "pid-approval": "initiate",
    "hiring-request": "initiate",
    "resource-mobilization": "execute",
    "neo-training": "execute",
    "knowledge-transfer": "plan",
    "volume-transfer": "execute",
    "hypercare": "monitor_control",
    "hypercare-exit": "monitor_control",
    "sign-off": "close_realize_value",
    "capacity-release": "close_realize_value",
}

# Fixed Migration Key Steps, classified using the reference lifecycle stages.
TEMPLATE_TASKS = [
    {"id": "business-case", "name": "Business Case (Memo)", "lifecycleStage": "initiate"},
    {"id": "fbp-approval", "name": "FBP approval", "lifecycleStage": "initiate"},
    {"id": "functional-head", "name": "Functional head approval", "lifecycleStage": "initiate"},
    {"id": "elt-approval", "name": "ELT approval", "lifecycleStage": "initiate"},
    {"id": "gsc-head", "name": "GSC Head -1 approval", "lifecycleStage": "initiate"},
    {
        "id": "opportunity-assessment",
        "name": "Opportunity Assessment (Detailed task scoping)",
        "lifecycleStage": "initiate",
    },
    {"id": "pid-approval", "name": "PID Approval", "lifecycleStage": "initiate"},
    {"id": "hiring-request", "name": "Hiring Request approval", "lifecycleStage": "initiate"},
    {"id": "resource-mobilization", "name": "Resource mobilization", "lifecycleStage": "execute"},
    {
        "id": "neo-training",
        "name": "NEO + GSC L&D business & training stage",
        "lifecycleStage": "execute",
    },
    {
        "id": "knowledge-transfer",
        "name": "Knowledge Transfer Business + System Training sessions + Assessments",
        "lifecycleStage": "plan",
    },
    {
        "id": "volume-transfer",
        "name": "Volume Transfer/Ramp-up stage",
        "lifecycleStage": "execute",
    },
    {"id": "hypercare", "name": "Hypercare stage", "lifecycleStage": "monitor_control"},
    {
        "id": "hypercare-exit",
        "name": "Hypercare Exit Success Criteria Review",
        "lifecycleStage": "monitor_control",
    },
    {
        "id": "sign-off",
        "name": "Migration Sign-off recommendation",
        "lifecycleStage": "close_realize_value",
    },
    {
        "id": "capacity-release",
        "name": "Recommended soonest Capacity Release",
        "lifecycleStage": "close_realize_value",
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


def _actual_from_date(plan: dict | None, actual_date, created_at) -> dict | None:
    """Map a completion date recorded outside Gantt to its Actual week range."""
    completed_week = _week_index_for_date(created_at, actual_date)
    if completed_week is None:
        return None
    start = min(int(plan["startWeek"]), completed_week) if plan else completed_week
    return _range_dict(start, completed_week)


def build_template_tasks(
    created_at=None, business_case_submitted_at=None
) -> list[dict]:
    """Return classified template tasks with empty Plan bars by default.

    The Business Case task's Actual is auto-filled from the intake's
    business_case_submission_date, since that submission already happened
    outside the Gantt page.
    """
    tasks = []
    for task in TEMPLATE_TASKS:
        actual = None
        actual_status = None
        if task["id"] == "business-case" and business_case_submitted_at:
            actual = _actual_from_date(None, business_case_submitted_at, created_at)
        tasks.append(
            {
                "id": task["id"],
                "name": task["name"],
                "lifecycleStage": task["lifecycleStage"],
                "plan": None,
                "actual": actual,
                "actualStatus": actual_status,
                "comments": [],
            }
        )
    return tasks


def merge_gantt_tasks_with_template(
    saved_tasks=None, created_at=None, business_case_submitted_at=None
) -> tuple[list[dict], list[dict]]:
    """
    Build display tasks from saved plan when present; otherwise use template.

    - No saved plan (None): return the full template with empty Plan.
    - Saved list (including empty): authoritative order / membership.
      Template ids keep their default lifecycle stage; custom / duplicated ids
      keep their saved stage and names.
    Returns (merged_tasks, template_tasks).
    """
    baseline = build_template_tasks(
        created_at=created_at, business_case_submitted_at=business_case_submitted_at
    )
    baseline_by_id = {task["id"]: task for task in baseline}

    if not isinstance(saved_tasks, list):
        return baseline, baseline

    merged: list[dict] = []
    for saved in saved_tasks:
        if not isinstance(saved, dict):
            continue
        task_id = str(saved.get("id") or "").strip()
        if not task_id:
            continue

        base = baseline_by_id.get(task_id)
        saved_name = str(saved.get("name") or "").strip()
        lifecycle_stage = str(saved.get("lifecycleStage") or "").strip()

        if base:
            # Correct the legacy typo without overwriting intentional custom names.
            name = base["name"] if saved_name == "ELT approg" else (saved_name or base["name"])
            default_stage = base["lifecycleStage"]
        else:
            name = saved_name or "Untitled stage"
            default_stage = "initiate"

        # Nested plan/actual, or legacy flat startWeek/endWeek as Plan.
        if "plan" in saved or "actual" in saved:
            if "plan" in saved and saved.get("plan") is None:
                plan = None
            else:
                plan = _parse_range(saved.get("plan"), fallback=None)
            actual_raw = _parse_range(saved.get("actual"), fallback=None)
        elif "startWeek" in saved or "endWeek" in saved:
            plan = _parse_range(
                {"startWeek": saved.get("startWeek"), "endWeek": saved.get("endWeek")},
                fallback=None,
            )
            actual_raw = None
        else:
            plan = None
            actual_raw = None

        actual = actual_raw
        # Business Case submission is tracked on its own page, not in Gantt.
        if not actual and task_id == "business-case" and business_case_submitted_at:
            actual = _actual_from_date(plan, business_case_submitted_at, created_at)
        comments = _normalize_comments(saved.get("comments"))

        merged.append(
            {
                "id": task_id,
                "name": name,
                "lifecycleStage": (
                    lifecycle_stage if lifecycle_stage in LIFECYCLE_STAGE_IDS else default_stage
                ),
                "plan": plan,
                "actual": actual,
                "actualStatus": _actual_status(plan, actual),
                "comments": comments,
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
        if not name:
            raise ValueError(f"Each task requires a name ({task_id}).")
        if task_id in seen:
            raise ValueError(f"Duplicate task id: {task_id}")
        seen.add(task_id)

        # Plan is editable and may be empty (null) for duplicated stages.
        if "plan" in item and item.get("plan") is None:
            plan = None
        elif isinstance(item.get("plan"), dict):
            plan = _parse_range(item.get("plan"))
        elif "startWeek" in item or "endWeek" in item:
            plan = _parse_range(
                {"startWeek": item.get("startWeek"), "endWeek": item.get("endWeek")}
            )
        else:
            plan = None

        lifecycle_stage = str(item.get("lifecycleStage") or "").strip()
        if not lifecycle_stage:
            lifecycle_stage = DEFAULT_LIFECYCLE_STAGE_BY_TASK_ID.get(task_id, "initiate")
        if lifecycle_stage not in LIFECYCLE_STAGE_IDS:
            raise ValueError(f"Invalid lifecycle stage for task {task_id}.")

        actual = _parse_range(item.get("actual"), fallback=None)

        comments = _normalize_comments(item.get("comments"))

        payload = {
            "id": task_id,
            "name": name,
            "lifecycleStage": lifecycle_stage,
            "plan": plan,
            "actual": actual,
            "comments": comments,
        }
        normalized.append(payload)
    return normalized


def _normalize_comments(raw_comments) -> list[dict]:
    """Normalize Plan-change comment history (append-only log per stage)."""
    if not isinstance(raw_comments, list):
        return []
    normalized = []
    for entry in raw_comments:
        if not isinstance(entry, dict):
            continue
        text = str(entry.get("text") or "").strip()
        if not text:
            continue
        comment_id = str(entry.get("id") or "").strip() or None
        at = str(entry.get("at") or "").strip() or None
        normalized.append(
            {
                "id": comment_id,
                "at": at,
                "text": text[:500],
                "updatedBy": (
                    str(entry.get("updatedBy") or entry.get("updated_by") or "").strip()[:200]
                    or None
                ),
                "fromPlan": _parse_range(entry.get("fromPlan"), fallback=None),
                "toPlan": _parse_range(entry.get("toPlan"), fallback=None),
            }
        )
    return normalized


def _comment_identity(entry: dict) -> str:
    """Stable key so merge can dedupe without dropping legitimate repeats of same text."""
    comment_id = str(entry.get("id") or "").strip()
    if comment_id:
        return f"id:{comment_id}"
    at = str(entry.get("at") or "").strip()
    text = str(entry.get("text") or "").strip()
    from_plan = entry.get("fromPlan") or {}
    to_plan = entry.get("toPlan") or {}
    return (
        f"fp:{at}|{text}|"
        f"{from_plan.get('startWeek')}-{from_plan.get('endWeek')}|"
        f"{to_plan.get('startWeek')}-{to_plan.get('endWeek')}"
    )


def _merge_comments(existing_comments, incoming_comments) -> list[dict]:
    """
    Append-only merge: keep prior history, add new entries, never replace with a shorter list.
    Caps length to MAX_PLAN_COMMENTS_PER_TASK (keeps newest).
    """
    merged: list[dict] = []
    seen: set[str] = set()
    for entry in list(existing_comments or []) + list(incoming_comments or []):
        if not isinstance(entry, dict):
            continue
        key = _comment_identity(entry)
        if key in seen:
            continue
        seen.add(key)
        merged.append(entry)
    if len(merged) > MAX_PLAN_COMMENTS_PER_TASK:
        merged = merged[-MAX_PLAN_COMMENTS_PER_TASK:]
    return merged


def _merge_saved_task_comments(existing_tasks, incoming_tasks) -> list[dict]:
    """Preserve per-stage comment history across saves (by task id)."""
    if not isinstance(existing_tasks, list):
        return incoming_tasks
    existing_by_id = {}
    for item in existing_tasks:
        if not isinstance(item, dict):
            continue
        task_id = str(item.get("id") or "").strip()
        if task_id:
            existing_by_id[task_id] = _normalize_comments(item.get("comments"))

    merged_tasks = []
    for task in incoming_tasks:
        task_id = task.get("id")
        prior = existing_by_id.get(task_id, [])
        incoming = task.get("comments") or []
        merged_tasks.append(
            {
                **task,
                "comments": _merge_comments(prior, incoming),
            }
        )
    return merged_tasks


def _normalize_meta(raw_meta):
    if raw_meta is None:
        return {}
    if not isinstance(raw_meta, dict):
        raise ValueError("meta must be an object.")

    normalized = {}
    for key in META_TEXT_KEYS:
        if key in raw_meta:
            normalized[key] = str(raw_meta.get(key) or "").strip()
    for key in META_NUMBER_KEYS:
        if key not in raw_meta:
            continue
        value = raw_meta[key]
        if value is None or value == "":
            normalized[key] = ""
            continue
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid number for meta.{key}.") from exc
        normalized[key] = int(number) if number.is_integer() else number
    return normalized


def _serialize_plan(
    plan: Optional[ProjectGanttPlan],
    project: MigrationIntakeSubmission,
) -> dict:
    mid = (project.migration_request_id or "").strip()
    saved_tasks = plan.tasks if plan else None
    tasks, template_tasks = merge_gantt_tasks_with_template(
        saved_tasks,
        created_at=project.created_at,
        business_case_submitted_at=project.business_case_submission_date,
    )
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
        "barTypes": BAR_TYPE_META,
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
        existing = ProjectGanttPlan.objects.filter(project=project).first()
        # Keep full Plan-comment history per stage (append-only merge with DB).
        if existing:
            tasks = _merge_saved_task_comments(existing.tasks, tasks)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    plan, _created = ProjectGanttPlan.objects.update_or_create(
        project=project,
        defaults={
            "tasks": tasks,
            "migration_request_id": project.migration_request_id or "",
        },
    )
    return Response(_serialize_plan(plan, project))
