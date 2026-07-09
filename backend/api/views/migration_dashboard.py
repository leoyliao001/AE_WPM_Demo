"""
Migration dashboard API views.

Frontend pages: /migration-dashboard, /migration-dashboard/:id
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import MigrationIntakeSubmission
from api.services.migration_dashboard import (
    build_dashboard_summary,
    serialize_project_detail,
    serialize_project_overview,
)


@api_view(["GET"])
def list_projects(request):
    """GET /api/migration-dashboard/projects/ — submitted migration intake overview."""
    submissions = list(MigrationIntakeSubmission.objects.all())
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
