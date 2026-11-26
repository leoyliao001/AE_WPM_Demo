from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

from api.models import LessonLearnt, MigrationIntakeSubmission
from api.permissions.attributes_access import get_request_email, normalize_email, require_attributes_access
from api.services.project_artefacts import project_permissions


TEXT_FIELDS = {
    "happened": "What happened?",
    "learned": "What did we learn?",
    "nextTime": "What should we do differently next time?",
}
SELECT_FIELDS = {
    "type": (LessonLearnt.TYPE_CHOICES, "Type"),
    "phase": (LessonLearnt.PHASE_CHOICES, "Phase"),
    "relatedArtefact": (LessonLearnt.ARTEFACT_CHOICES, "Related artefact"),
    "relevantFor": (LessonLearnt.RELEVANCE_CHOICES, "Relevant for"),
}
MAX_TEXT_LENGTH = 5000


def _serialize_lesson(lesson):
    return {
        "id": lesson.pk,
        "happened": lesson.happened,
        "learned": lesson.learned,
        "nextTime": lesson.next_time,
        "type": lesson.lesson_type,
        "phase": lesson.phase,
        "relatedArtefact": lesson.related_artefact,
        "relevantFor": lesson.relevant_for,
        "createdBy": lesson.created_by,
        "createdAt": lesson.created_at.isoformat(),
    }


def _validate_payload(payload):
    values = {}
    for key, label in TEXT_FIELDS.items():
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} is required.")
        value = value.strip()
        if len(value) > MAX_TEXT_LENGTH:
            raise ValueError(f"{label} must be {MAX_TEXT_LENGTH} characters or fewer.")
        values[key] = value

    for key, (choices, label) in SELECT_FIELDS.items():
        value = payload.get(key)
        allowed = {choice[0] for choice in choices}
        if not isinstance(value, str) or value not in allowed:
            raise ValueError(f"Select a valid {label.lower()}.")
        values[key] = value
    return values


@api_view(["GET", "POST"])
def lessons_learnt(request, project_id):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required."}, status=401)

    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if not project:
        return Response({"error": "Project not found."}, status=404)

    permissions = project_permissions(project, email, "resources")
    if not permissions["view"]:
        return Response(
            {"error": "Only the project requestor, Project Team or users with project access can view Lessons Learnt."},
            status=403,
        )

    if request.method == "GET":
        lesson = LessonLearnt.objects.filter(project=project).first()
        return Response({
            "projectId": project.pk,
            "projectName": project.project_name,
            "saved": lesson is not None,
            "lesson": _serialize_lesson(lesson) if lesson else None,
        })

    if not isinstance(request.data, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    try:
        values = _validate_payload(request.data)
    except ValueError as error:
        return Response({"error": str(error)}, status=400)

    with transaction.atomic():
        project = MigrationIntakeSubmission.objects.select_for_update().filter(pk=project.pk).first()
        if not project:
            return Response({"error": "Project not found."}, status=404)
        existing = LessonLearnt.objects.filter(project=project).first()
        if existing:
            return Response({
                "error": "A lesson has already been submitted for this project.",
                "lesson": _serialize_lesson(existing),
            }, status=409)
        lesson = LessonLearnt.objects.create(
            project=project,
            happened=values["happened"],
            learned=values["learned"],
            next_time=values["nextTime"],
            lesson_type=values["type"],
            phase=values["phase"],
            related_artefact=values["relatedArtefact"],
            relevant_for=values["relevantFor"],
            created_by=email,
        )
    return Response({"lesson": _serialize_lesson(lesson)}, status=201)


def _serialize_admin_lesson(lesson):
    return {
        **_serialize_lesson(lesson),
        "projectId": lesson.project_id,
        "migrationRequestId": lesson.project.migration_request_id,
        "projectName": lesson.project.project_name,
        "requestor": lesson.project.requestor,
        "updatedAt": lesson.updated_at.isoformat(),
    }


def _project_id_from_payload(payload):
    value = payload.get("projectId")
    if type(value) is int:
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise ValueError("Select a valid project.")


@api_view(["GET", "POST"])
@require_attributes_access("lessons_learnt")
def maintain_lessons_learnt(request):
    if request.method == "GET":
        rows = [
            _serialize_admin_lesson(lesson)
            for lesson in LessonLearnt.objects.select_related("project").order_by("-created_at", "-id")
        ]
        return Response({"rows": rows, "count": len(rows)})

    if not isinstance(request.data, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    try:
        project_id = _project_id_from_payload(request.data)
        values = _validate_payload(request.data)
    except ValueError as error:
        return Response({"error": str(error)}, status=400)

    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if project is None:
        return Response({"error": "Project not found."}, status=404)

    lesson = LessonLearnt.objects.create(
        project=project,
        happened=values["happened"],
        learned=values["learned"],
        next_time=values["nextTime"],
        lesson_type=values["type"],
        phase=values["phase"],
        related_artefact=values["relatedArtefact"],
        relevant_for=values["relevantFor"],
        created_by=request.attributes_email,
    )
    return Response({"lesson": _serialize_admin_lesson(lesson)}, status=201)


@api_view(["PUT", "DELETE"])
@require_attributes_access("lessons_learnt")
def maintain_lesson_learnt(request, lesson_id):
    if request.method == "DELETE":
        deleted, _ = LessonLearnt.objects.filter(pk=lesson_id).delete()
        if not deleted:
            return Response({"error": "Lesson not found."}, status=404)
        return Response({"deleted": True})

    if not isinstance(request.data, dict):
        return Response({"error": "Request body must be an object."}, status=400)
    try:
        project_id = _project_id_from_payload(request.data)
        values = _validate_payload(request.data)
    except ValueError as error:
        return Response({"error": str(error)}, status=400)

    project = MigrationIntakeSubmission.objects.filter(pk=project_id).first()
    if project is None:
        return Response({"error": "Project not found."}, status=404)

    with transaction.atomic():
        lesson = LessonLearnt.objects.select_for_update().filter(pk=lesson_id).first()
        if lesson is None:
            return Response({"error": "Lesson not found."}, status=404)
        lesson.project = project
        lesson.happened = values["happened"]
        lesson.learned = values["learned"]
        lesson.next_time = values["nextTime"]
        lesson.lesson_type = values["type"]
        lesson.phase = values["phase"]
        lesson.related_artefact = values["relatedArtefact"]
        lesson.relevant_for = values["relevantFor"]
        lesson.save()
    return Response({"lesson": _serialize_admin_lesson(lesson)})
