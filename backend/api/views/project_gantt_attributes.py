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
    ALLOWED_PHASE_IDS,
    META_NUMBER_KEYS,
    META_TEXT_KEYS,
    MAX_WEEK,
    MIN_WEEK,
    _normalize_meta,
)

TASK_COLUMNS = [
    ("task_id", "Task ID"),
    ("name", "Task Name"),
    ("startWeek", "Start Week"),
    ("endWeek", "End Week"),
    ("phaseId", "Phase ID"),
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


def _serialize_task_row(task: dict) -> dict:
    return {
        "id": str(task.get("id") or ""),
        "task_id": str(task.get("id") or ""),
        "name": str(task.get("name") or ""),
        "startWeek": task.get("startWeek", ""),
        "endWeek": task.get("endWeek", ""),
        "phaseId": str(task.get("phaseId") or "opportunity"),
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
        start_raw = item.get("startWeek")
        end_raw = item.get("endWeek")
        phase_id = str(item.get("phaseId") or "").strip() or "opportunity"

        # Skip completely blank rows
        if (
            not name
            and not task_id
            and (start_raw in (None, "", False))
            and (end_raw in (None, "", False))
        ):
            continue

        if not name:
            raise ValueError(f"Task row {index + 1}: Task Name is required.")

        if not task_id:
            task_id = _slug_task_id(name, used_ids)
        elif task_id in used_ids:
            raise ValueError(f"Duplicate Task ID: {task_id}")
        else:
            used_ids.add(task_id)

        try:
            start = int(start_raw)
            end = int(end_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Task {task_id}: invalid week range.") from exc

        if start > end:
            start, end = end, start
        if start < MIN_WEEK or end > MAX_WEEK:
            raise ValueError(
                f"Task {task_id}: week range must be between {MIN_WEEK} and {MAX_WEEK}."
            )

        if phase_id not in ALLOWED_PHASE_IDS:
            raise ValueError(f"Task {task_id}: invalid phaseId '{phase_id}'.")

        normalized.append(
            {
                "id": task_id,
                "name": name,
                "startWeek": start,
                "endWeek": end,
                "phaseId": phase_id,
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
    if plan and isinstance(plan.meta, dict):
        meta.update({k: plan.meta.get(k, meta.get(k)) for k in meta})

    rows = [_serialize_task_row(task) for task in (plan.tasks or [])] if plan else []

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
            "phase_options": sorted(ALLOWED_PHASE_IDS),
            "rows": rows,
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
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        meta = _normalize_meta(request.data.get("meta") or {})
        # Keep unspecified meta keys from existing plan / defaults
        existing = ProjectGanttPlan.objects.filter(project=project).first()
        merged_meta = _default_meta()
        if existing and isinstance(existing.meta, dict):
            merged_meta.update(existing.meta)
        for key in (*META_TEXT_KEYS, *META_NUMBER_KEYS):
            if key in meta:
                merged_meta[key] = meta[key]
        tasks = _normalize_task_rows(request.data.get("tasks") or request.data.get("uniqueData") or [])
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

    return Response(
        {
            "status": "success",
            "created": created,
            "project_id": project.id,
            "migration_request_id": project.migration_request_id,
            "meta": plan.meta or {},
            "rows": [_serialize_task_row(task) for task in (plan.tasks or [])],
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
        }
    )
