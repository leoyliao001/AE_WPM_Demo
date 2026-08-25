"""
Migration intake API views.

Frontend page: /migration-intake
"""

import logging
import threading

from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.permissions.attributes_access import get_request_email
from api.services.migration_intake import create_submission_from_payload
from api.services.migration_intake_notifications import send_migration_intake_notification

logger = logging.getLogger(__name__)

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
        "products": "At least one product is required.",
        "languageDependencies": "At least one language is required.",
    }
    for field, message in list_fields.items():
        if not payload.get(field):
            return message

    if payload.get("locationStrategyCustom"):
        if not payload.get("customLocationStrategies"):
            return "Custom location strategy is required."
        if not str(payload.get("customLocationStrategyJustification", "")).strip():
            return "Custom location strategy justification is required."
        if not (payload.get("customApprovalFile") or {}).get("name"):
            return "Custom location strategy approval attachment is required."
    elif not payload.get("defaultLocationStrategies"):
        return "At least one location strategy is required."

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

    signed_in_email = get_request_email(request)

    def _send_notification():
        try:
            send_migration_intake_notification(
                submission,
                signed_in_email=signed_in_email,
            )
        except Exception:
            logger.exception(
                "Failed to send migration intake notification for %s",
                submission.migration_request_id,
            )

    thread = threading.Thread(target=_send_notification, daemon=True)
    thread.start()

    return Response(
        {
            "ok": True,
            "id": submission.id,
            "migrationRequestId": submission.migration_request_id,
            "emailSent": "queued",
            "message": (
                f"Migration request {submission.migration_request_id} "
                "has been saved to the database. "
                "Email notification is being sent in the background."
            ),
        },
        status=status.HTTP_201_CREATED,
    )
