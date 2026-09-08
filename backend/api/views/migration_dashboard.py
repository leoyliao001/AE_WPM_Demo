"""
Migration dashboard API views.

Frontend pages: /migration-dashboard, /migration-dashboard/:id
Also used by /project-dashboard with ?mine=1 (current user's projects only).
"""

import logging
import threading

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from django.http import FileResponse, Http404
from django.utils import timezone

from api.models import ApprovalWorkflow, MigrationIntakeSubmission
from api.permissions.attributes_access import get_request_email, normalize_email
from api.services.migration_dashboard import (
    build_dashboard_summary,
    serialize_business_case_file,
    serialize_project_detail,
    serialize_project_overview,
)
from api.services.approval_notifications import send_next_stage_notification

logger = logging.getLogger(__name__)

MAX_BUSINESS_CASE_BYTES = 20 * 1024 * 1024


def _wants_mine_only(request) -> bool:
    raw = (request.query_params.get("mine") or "").strip().lower()
    return raw in {"1", "true", "yes"}


@api_view(["GET"])
def list_projects(request):
    """GET /api/migration-dashboard/projects/ — submitted migration intake overview.

    Query params:
      mine=1 — only projects whose requestor matches the signed-in SSO email
    """
    qs = MigrationIntakeSubmission.objects.all()

    if _wants_mine_only(request):
        email = get_request_email(request)
        if not email:
            return Response(
                {"error": "Sign in required. Missing SSO email."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        qs = qs.filter(requestor__iexact=normalize_email(email))

    submissions = list(qs)
    rows = [serialize_project_overview(item) for item in submissions]

    return Response(
        {
            "count": len(rows),
            "summary": build_dashboard_summary(submissions),
            "rows": rows,
        }
    )


@api_view(["GET"])
def project_detail(request, project_id: int):
    """GET /api/migration-dashboard/projects/<id>/ — full project detail."""
    try:
        submission = MigrationIntakeSubmission.objects.get(pk=project_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response(serialize_project_detail(submission))


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def submit_business_case(request, project_id: int):
    """Record final Business Case submission and begin the approval timeline."""
    try:
        submission = MigrationIntakeSubmission.objects.get(pk=project_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED)
    if email != normalize_email(submission.requestor):
        return Response({"error": "Only the project requestor can submit the final Business Case."}, status=status.HTTP_403_FORBIDDEN)

    submitted_at = timezone.now()
    upload = request.FILES.get("file")
    if upload is not None:
        allowed = (".doc", ".docx", ".pdf")
        if not upload.name.lower().endswith(allowed):
            return Response(
                {"error": "Only .doc, .docx or .pdf files are accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload.size > MAX_BUSINESS_CASE_BYTES:
            return Response(
                {"error": "File is larger than the 20 MB limit."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        submission.business_case_file.save(upload.name, upload, save=False)
        submission.business_case_file_name = upload.name
        submission.business_case_file_size = upload.size

    submission.business_case_submission_date = submitted_at
    update_fields = [
        "business_case_submission_date",
        "business_case_file",
        "business_case_file_name",
        "business_case_file_size",
        "updated_at",
    ]
    # Move the dashboard milestone stepper forward now that the business
    # case is in; never downgrade a status that has already progressed further.
    if submission.status == "new":
        submission.status = "in_review"
        update_fields.append("status")
    submission.save(update_fields=update_fields)
    workflow, _created = ApprovalWorkflow.objects.get_or_create(
        migration_request_id=submission.migration_request_id
    )
    workflow.business_case_submitted_date = submitted_at
    workflow.save(update_fields=["business_case_submitted_date", "updated_at"])

    def notify_area_head():
        try:
            send_next_stage_notification(submission, "area_head")
        except Exception:
            logger.exception("Failed to notify Area Head for %s", submission.migration_request_id)

    threading.Thread(target=notify_area_head, daemon=True).start()
    return Response(
        {
            "status": "success",
            "submitted_at": submitted_at,
            "project_status": submission.status,
            "file": serialize_business_case_file(submission),
        }
    )


@api_view(["GET"])
def download_business_case(request, project_id: int):
    """Serve the uploaded final Business Case attachment."""
    try:
        submission = MigrationIntakeSubmission.objects.get(pk=project_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    if not submission.business_case_file:
        return Response({"error": "No Business Case attachment on file."}, status=status.HTTP_404_NOT_FOUND)

    try:
        handle = submission.business_case_file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("Business Case attachment is missing from storage.")

    filename = submission.business_case_file_name or submission.business_case_file.name.rsplit("/", 1)[-1]
    return FileResponse(handle, as_attachment=True, filename=filename)
