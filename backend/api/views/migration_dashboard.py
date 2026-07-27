"""
Migration dashboard API views.

Frontend pages: /migration-dashboard, /migration-dashboard/:id
Also used by /project-dashboard with ?mine=1 (current user's projects only).
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationIntakeSubmission
from api.permissions.attributes_access import get_request_email, normalize_email
from api.services.migration_dashboard import (
    build_dashboard_summary,
    serialize_project_detail,
    serialize_project_overview,
)


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
