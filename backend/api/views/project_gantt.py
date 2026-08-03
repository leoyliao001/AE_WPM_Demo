"""
Project Gantt API — per-project editable task week spans + summary meta.

Migration Key Steps are a fixed template (Excel / Project Gantt sheet). Saved
plan tasks are merged by id to preserve week/phase edits.

GET  /api/migration-dashboard/projects/<id>/gantt/
PUT  /api/migration-dashboard/projects/<id>/gantt/
"""

from typing import Optional
from datetime import date, datetime, timedelta
import re

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

# Built-in Status legend (id / label / color). Custom phases are stored per project.
BUILTIN_PHASES = [
    {"id": "opportunity", "label": "Opportunity Assessment", "color": "#6E6E6E"},
    {"id": "onboarding", "label": "Resource Onboarding", "color": "#0086E6"},
    {"id": "gss-training", "label": "GSS Training", "color": "#A3450A"},
    {"id": "knowledge-transfer", "label": "Knowledge Transfer", "color": "#FFA008"},
    {"id": "volume-rampup", "label": "Volume Ramp-up", "color": "#1A9EBE"},
    {"id": "hypercare", "label": "Hypercare", "color": "#001A75"},
    {"id": "closure", "label": "Project Closure", "color": "#00C853"},
]

HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
CUSTOM_PHASE_ID_RE = re.compile(r"^custom-[a-z0-9-]{2,48}$")

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


def _slugify_phase_id(label: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (label or "").strip().lower()).strip("-") or "status"
    return f"custom-{base[:40]}"


def _normalize_custom_phases(raw_phases) -> list[dict]:
    """Normalize user-defined Status options: [{id, label, color}, ...]."""
    if raw_phases is None:
        return []
    if not isinstance(raw_phases, list):
        raise ValueError("customPhases must be a list.")

    normalized: list[dict] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_phases):
        if not isinstance(item, dict):
            raise ValueError(f"customPhases[{index}] must be an object.")

        label = str(item.get("label") or "").strip()
        if not label:
            raise ValueError(f"customPhases[{index}]: label is required.")
        if len(label) > 80:
            raise ValueError(f"customPhases[{index}]: label is too long (max 80).")

        phase_id = str(item.get("id") or "").strip()
        if not phase_id:
            phase_id = _slugify_phase_id(label)
        if phase_id in ALLOWED_PHASE_IDS:
            raise ValueError(f"customPhases[{index}]: id '{phase_id}' is reserved.")
        if not CUSTOM_PHASE_ID_RE.match(phase_id):
            # Allow auto-generated ids that may include a short suffix
            if not phase_id.startswith("custom-"):
                phase_id = f"custom-{phase_id}"
            phase_id = re.sub(r"[^a-z0-9-]", "-", phase_id.lower()).strip("-")
            if not CUSTOM_PHASE_ID_RE.match(phase_id):
                phase_id = f"{_slugify_phase_id(label)}-{index + 1}"
        if phase_id in seen:
            raise ValueError(f"Duplicate custom phase id: {phase_id}")
        seen.add(phase_id)

        color = str(item.get("color") or "").strip() or "#64748B"
        if not HEX_COLOR_RE.match(color):
            raise ValueError(f"customPhases[{index}]: color must be a hex value like #RRGGBB.")

        normalized.append(
            {
                "id": phase_id,
                "label": label,
                "color": color.upper() if len(color) == 7 else color,
                "custom": True,
            }
        )
    return normalized


def _extract_custom_phases_from_meta(meta) -> list[dict]:
    if not isinstance(meta, dict):
        return []
    try:
        return _normalize_custom_phases(meta.get("customPhases"))
    except ValueError:
        return []


def _allowed_phase_ids(custom_phases: list[dict] | None = None) -> set[str]:
    allowed = set(ALLOWED_PHASE_IDS)
    for phase in custom_phases or []:
        phase_id = str(phase.get("id") or "").strip()
        if phase_id:
            allowed.add(phase_id)
    return allowed


def _merged_phases(custom_phases: list[dict] | None = None) -> list[dict]:
    phases = [
        {
            "id": p["id"],
            "label": p["label"],
            "color": p["color"],
            "custom": False,
        }
        for p in BUILTIN_PHASES
    ]
    for phase in custom_phases or []:
        phases.append(
            {
                "id": phase["id"],
                "label": phase["label"],
                "color": phase["color"],
                "custom": True,
            }
        )
    return phases


def merge_gantt_tasks_with_template(
    saved_tasks=None, allowed_phase_ids: set[str] | None = None
) -> tuple[list[dict], list[dict]]:
    """
    Overlay saved week/phase onto the fixed template by task id.
    Returns (merged_tasks, baseline_tasks).
    """
    allowed = set(allowed_phase_ids) if allowed_phase_ids is not None else set(ALLOWED_PHASE_IDS)
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
        if phase_id not in allowed:
            phase_id = base["phaseId"] if base["phaseId"] in allowed else DEFAULT_TASK_PHASE

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


def _normalize_tasks(raw_tasks, allowed_phase_ids: set[str] | None = None):
    if not isinstance(raw_tasks, list):
        raise ValueError("tasks must be a list.")

    allowed = set(allowed_phase_ids) if allowed_phase_ids is not None else set(ALLOWED_PHASE_IDS)
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
        if phase_id and phase_id not in allowed:
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
    saved_meta = (plan.meta if plan else {}) or {}
    custom_phases = _extract_custom_phases_from_meta(saved_meta)
    allowed = _allowed_phase_ids(custom_phases)
    saved_tasks = plan.tasks if plan else None
    tasks, template_tasks = merge_gantt_tasks_with_template(saved_tasks, allowed)
    weeks = build_gantt_weeks(project.created_at)
    start_week = weeks[0]["calendarWeekNumber"] if weeks else DEFAULT_CALENDAR_START_WEEK
    # Public meta excludes customPhases (returned separately).
    public_meta = {k: v for k, v in saved_meta.items() if k != "customPhases"}
    return {
        "project_id": project.id,
        "migration_request_id": mid or None,
        "saved": bool(plan),
        "tasks": tasks,
        "template_tasks": template_tasks,
        "weeks": weeks,
        "calendar_start_week": start_week,
        "intake_created_at": project.created_at.isoformat() if project.created_at else None,
        "customPhases": custom_phases,
        "phases": _merged_phases(custom_phases),
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
        # Prefer explicit customPhases; fall back to existing plan meta.
        existing = ProjectGanttPlan.objects.filter(project=project).first()
        if "customPhases" in request.data:
            custom_phases = _normalize_custom_phases(request.data.get("customPhases"))
        else:
            custom_phases = _extract_custom_phases_from_meta(
                existing.meta if existing else {}
            )
        allowed = _allowed_phase_ids(custom_phases)
        tasks = _normalize_tasks(request.data.get("tasks"), allowed)
        meta = _normalize_meta(request.data.get("meta"))
        meta["customPhases"] = custom_phases
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
