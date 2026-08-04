"""
Project Gantt Attributes API — load / save by Migration Request ID.

GET  /api/project-gantt-attributes/?migration_request_id=...
POST /api/project-gantt-attributes/data/
"""

from __future__ import annotations

import re

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationIntakeSubmission, ProjectGanttPlan
from api.permissions.attributes_access import require_attributes_access
from api.views.project_gantt import (
    BAR_TYPE_META,
    META_NUMBER_KEYS,
    META_TEXT_KEYS,
    MAX_WEEK,
    MIN_WEEK,
    _normalize_meta,
    merge_gantt_tasks_with_template,
)

TASK_COLUMNS = [
    ("task_id", "Task ID"),
    ("name", "Task Name"),
    ("standardStartWeek", "Standard Start"),
    ("standardEndWeek", "Standard End"),
    ("planStartWeek", "Plan Start"),
    ("planEndWeek", "Plan End"),
    ("actualStartWeek", "Actual Start"),
    ("actualEndWeek", "Actual End"),
    ("completedAt", "Completed At"),
    ("actualStatus", "Actual Status"),
]

META_COLUMNS = [
    ("projectPhase", "Project Phase"),
    ("scope", "Scope"),
    ("migratableFte", "Migratable FTE"),
    ("learningCurve", "Learning Curve"),
    ("tlTmHc", "TL/TM HC"),
    ("mngrHc", "Mngr. HC"),
    ("totalWoBuffer", "Total wo/buffer"),
    ("total", "Total"),
]

SLUG_RE = re.compile(r"[^a-z0-9]+")


def _default_meta() -> dict:
    return {
        "projectPhase": "",
        "scope": "",
        "migratableFte": "",
        "learningCurve": "",
        "tlTmHc": "",
        "mngrHc": "",
        "totalWoBuffer": "",
        "total": "",
    }


def _range_value(task: dict, key: str, field: str):
    block = task.get(key)
    if not isinstance(block, dict):
        return ""
    value = block.get(field)
    return "" if value in (None, "") else value


def _serialize_task_row(task: dict) -> dict:
    return {
        "id": str(task.get("id") or ""),
        "task_id": str(task.get("id") or ""),
        "name": str(task.get("name") or ""),
        "standardStartWeek": _range_value(task, "standard", "startWeek"),
        "standardEndWeek": _range_value(task, "standard", "endWeek"),
        "planStartWeek": _range_value(task, "plan", "startWeek"),
        "planEndWeek": _range_value(task, "plan", "endWeek"),
        "actualStartWeek": _range_value(task, "actual", "startWeek"),
        "actualEndWeek": _range_value(task, "actual", "endWeek"),
        "completedAt": task.get("completedAt") or "",
        "actualStatus": task.get("actualStatus") or "",
    }


def _slug_task_id(name: str, used: set[str]) -> str:
    base = SLUG_RE.sub("-", (name or "").strip().lower()).strip("-") or "task"
    base = base[:48]
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def _parse_week(raw, label: str) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: invalid week.") from exc
    if value < MIN_WEEK or value > MAX_WEEK:
        raise ValueError(f"{label}: week must be between {MIN_WEEK} and {MAX_WEEK}.")
    return value


def _normalize_task_rows(raw_tasks) -> list[dict]:
    if not isinstance(raw_tasks, list):
        raise ValueError("tasks must be a list.")

    normalized: list[dict] = []
    used_ids: set[str] = set()

    for index, item in enumerate(raw_tasks):
        if not isinstance(item, dict):
            raise ValueError(f"Task row {index} must be an object.")

        name = str(item.get("name") or "").strip()
        task_id = str(item.get("task_id") or item.get("id") or "").strip()

        plan_start_raw = item.get("planStartWeek", item.get("startWeek"))
        plan_end_raw = item.get("planEndWeek", item.get("endWeek"))

        blank = (
            not name
            and not task_id
            and plan_start_raw in (None, "", False)
            and plan_end_raw in (None, "", False)
        )
        if blank:
            continue

        if not name:
            raise ValueError(f"Task row {index + 1}: Task Name is required.")

        if not task_id:
            task_id = _slug_task_id(name, used_ids)
        elif task_id in used_ids:
            raise ValueError(f"Duplicate Task ID: {task_id}")
        else:
            used_ids.add(task_id)

        plan_start = _parse_week(plan_start_raw, f"Task {task_id} Plan Start")
        plan_end = _parse_week(plan_end_raw, f"Task {task_id} Plan End")
        if plan_start > plan_end:
            plan_start, plan_end = plan_end, plan_start

        actual = None
        actual_start_raw = item.get("actualStartWeek")
        actual_end_raw = item.get("actualEndWeek")
        if actual_start_raw not in (None, "") or actual_end_raw not in (None, ""):
            a_start = _parse_week(
                actual_start_raw if actual_start_raw not in (None, "") else plan_start,
                f"Task {task_id} Actual Start",
            )
            a_end = _parse_week(
                actual_end_raw if actual_end_raw not in (None, "") else a_start,
                f"Task {task_id} Actual End",
            )
            if a_start > a_end:
                a_start, a_end = a_end, a_start
            actual = {"startWeek": a_start, "endWeek": a_end}

        completed_at = str(item.get("completedAt") or "").strip() or None

        normalized.append(
            {
                "id": task_id,
                "name": name,
                "plan": {"startWeek": plan_start, "endWeek": plan_end},
                "actual": actual,
                "completedAt": completed_at,
            }
        )

    return normalized


@api_view(["GET"])
@require_attributes_access("project_gantt")
def get_project_gantt_attributes(request):
    migration_request_id = str(request.query_params.get("migration_request_id") or "").strip()
    if not migration_request_id:
        return Response(
            {"error": "migration_request_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project = MigrationIntakeSubmission.objects.filter(
        migration_request_id__iexact=migration_request_id
    ).first()
    if not project:
        return Response(
            {
                "found": False,
                "error": f"No migration project found for '{migration_request_id}'.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    plan = ProjectGanttPlan.objects.filter(project=project).first()
    meta = _default_meta()
    saved_meta = (plan.meta if plan else {}) or {}
    if isinstance(saved_meta, dict):
        meta.update({k: saved_meta.get(k, meta.get(k)) for k in meta})

    merged_tasks, template_tasks = merge_gantt_tasks_with_template(
        plan.tasks if plan else None,
        created_at=project.created_at,
    )
    rows = [_serialize_task_row(task) for task in merged_tasks]

    return Response(
        {
            "found": True,
            "saved": bool(plan),
            "project_id": project.id,
            "migration_request_id": project.migration_request_id,
            "project_name": project.project_name,
            "meta": meta,
            "meta_columns": [{"key": key, "label": label} for key, label in META_COLUMNS],
            "columns": [{"key": key, "label": label} for key, label in TASK_COLUMNS],
            "bar_types": BAR_TYPE_META,
            "rows": rows,
            "template_task_count": len(template_tasks),
            "updated_at": plan.updated_at.isoformat() if plan and plan.updated_at else None,
        }
    )


@api_view(["POST"])
@require_attributes_access("project_gantt")
def save_project_gantt_attributes(request):
    migration_request_id = str(request.data.get("migration_request_id") or "").strip()
    if not migration_request_id:
        return Response(
            {"error": "migration_request_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project = MigrationIntakeSubmission.objects.filter(
        migration_request_id__iexact=migration_request_id
    ).first()
    if not project:
        return Response(
            {"error": f"No migration project found for '{migration_request_id}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        meta = _normalize_meta(request.data.get("meta") or {})
        existing = ProjectGanttPlan.objects.filter(project=project).first()
        merged_meta = _default_meta()
        if existing and isinstance(existing.meta, dict):
            merged_meta.update(
                {k: v for k, v in existing.meta.items() if k != "customPhases"}
            )
        for key in (*META_TEXT_KEYS, *META_NUMBER_KEYS):
            if key in meta:
                merged_meta[key] = meta[key]
        merged_meta.pop("customPhases", None)
        tasks = _normalize_task_rows(
            request.data.get("tasks") or request.data.get("uniqueData") or []
        )
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    plan, created = ProjectGanttPlan.objects.update_or_create(
        project=project,
        defaults={
            "migration_request_id": project.migration_request_id or "",
            "meta": merged_meta,
            "tasks": tasks,
        },
    )

    merged_tasks, _template = merge_gantt_tasks_with_template(
        plan.tasks, created_at=project.created_at
    )

    return Response(
        {
            "status": "success",
            "created": created,
            "project_id": project.id,
            "migration_request_id": project.migration_request_id,
            "meta": {
                k: v for k, v in (plan.meta or {}).items() if k != "customPhases"
            },
            "rows": [_serialize_task_row(task) for task in merged_tasks],
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
        }
    )
