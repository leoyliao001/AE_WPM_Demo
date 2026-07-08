"""
Migration intake API views.

Frontend page: /migration-intake
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["POST"])
def submit_intake(request):
    """POST /api/migration-intake/submit/ — accept a reviewed migration request payload."""
    payload = request.data
    migration_request_id = payload.get("migrationRequestId")

    if not migration_request_id:
        return Response(
            {"error": "migrationRequestId is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # TODO: persist to database / Project Attributes Database
    return Response(
        {
            "ok": True,
            "migrationRequestId": migration_request_id,
            "message": (
                f"Migration request {migration_request_id} has been received "
                "and will sync to the Project Attributes Database."
            ),
        },
        status=status.HTTP_201_CREATED,
    )
