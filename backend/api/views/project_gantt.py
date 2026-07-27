"""
Project Gantt API — per-project editable task week spans + summary meta.

GET  /api/migration-dashboard/projects/<id>/gantt/
PUT  /api/migration-dashboard/projects/<id>/gantt/
"""

from typing import Optional

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationIntakeSubmission, ProjectGanttPlan

MAX_WEEK = 44
MIN_WEEK = 1

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


def _serialize_plan(plan: Optional[ProjectGanttPlan], project_id: int) -> dict:
    if not plan:
        return {
            "project_id": project_id,
            "saved": False,
            "tasks": [],
            "meta": {},
            "updated_at": None,
        }
    return {
        "project_id": project_id,
        "saved": True,
        "tasks": plan.tasks or [],
        "meta": plan.meta or {},
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


@api_view(["GET", "PUT"])
def project_gantt(request, project_id: int):
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        plan = ProjectGanttPlan.objects.filter(project=project).first()
        return Response(_serialize_plan(plan, project.id))

    try:
        tasks = _normalize_tasks(request.data.get("tasks"))
        meta = _normalize_meta(request.data.get("meta"))
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    plan, _created = ProjectGanttPlan.objects.update_or_create(
        project=project,
        defaults={"tasks": tasks, "meta": meta},
    )
    return Response(_serialize_plan(plan, project.id))
