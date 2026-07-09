"""
Migration intake API views.

Frontend page: /migration-intake
"""

from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.services.migration_intake import create_submission_from_payload

REQUIRED_FIELDS = [
    "migrationRequestId",
    "projectName",
    "migrationType",
    "region",
    "function",
    "proposedScope",
    "fteNumber",
]


def _validate_payload(payload: dict) -> str | None:
    if not isinstance(payload, dict):
        return "Request body must be a JSON object."

    for field in REQUIRED_FIELDS:
        value = payload.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            return f"{field} is required."

    list_fields = {
        "areas": "At least one area is required.",
        "countries": "At least one country is required.",
        "locationStrategies": "At least one location strategy is required.",
        "products": "At least one product is required.",
        "languageDependencies": "At least one language is required.",
    }
    for field, message in list_fields.items():
        if not payload.get(field):
            return message

    if payload.get("supportingGscSitesCustom"):
        if not payload.get("customSupportingGscSites"):
            return "Custom supporting GSC sites are required."
        if not str(payload.get("customSupportingJustification", "")).strip():
            return "Custom supporting GSC sites justification is required."
        if not (payload.get("customApprovalFile") or {}).get("name"):
            return "Custom supporting GSC sites approval attachment is required."
    elif not payload.get("defaultSupportingGscSites"):
        return "At least one default supporting GSC site is required."

    return None


@api_view(["POST"])
def submit_intake(request):
    """POST /api/migration-intake/submit/ — persist a reviewed migration request."""
    payload = request.data
    error = _validate_payload(payload)
    if error:
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

    try:
        submission = create_submission_from_payload(payload)
    except IntegrityError:
        return Response(
            {
                "error": (
                    f"Migration request {payload.get('migrationRequestId')} "
                    "already exists."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )

    return Response(
        {
            "ok": True,
            "id": submission.id,
            "migrationRequestId": submission.migration_request_id,
            "message": (
                f"Migration request {submission.migration_request_id} "
                "has been saved to the database."
            ),
        },
        status=status.HTTP_201_CREATED,
    )
