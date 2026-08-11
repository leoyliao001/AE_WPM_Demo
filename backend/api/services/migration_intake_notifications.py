import logging
import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q

from api.models import MigrationIntakeSubmission, ProductOwnership

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+", re.I)


def _csv(values) -> str:
    return ", ".join([str(value).strip() for value in (values or []) if str(value).strip()])


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _extract_emails(value: str) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    seen = set()
    emails = []
    for match in EMAIL_RE.findall(text):
        email = _normalize_email(match)
        if not email or email in seen:
            continue
        seen.add(email)
        emails.append(email)
    return emails


def _manager_emails_for_submission(submission: MigrationIntakeSubmission) -> list[str]:
    region = str(submission.region or "").strip()
    areas = [str(area).strip() for area in (submission.areas or []) if str(area).strip()]

    if not region:
        return []

    qs = ProductOwnership.objects.filter(region=region)
    if areas:
        qs = qs.filter(Q(area__in=areas) | Q(area=""))

    recipients = []
    seen = set()
    for row in qs.order_by("id"):
        for email in _extract_emails(row.migration_manager):
            if email in seen:
                continue
            seen.add(email)
            recipients.append(email)
    return recipients


def resolve_notification_recipients(
    submission: MigrationIntakeSubmission,
    *,
    signed_in_email: str = "",
) -> list[str]:
    recipients = []
    seen = set()

    def add_many(values):
        for value in values:
            email = _normalize_email(value)
            if not email or email in seen:
                continue
            seen.add(email)
            recipients.append(email)

    add_many(getattr(settings, "MIGRATION_INTAKE_NOTIFY_TO", []) or [])
    add_many(_extract_emails(signed_in_email))
    add_many(_extract_emails(submission.requestor))
    add_many(_manager_emails_for_submission(submission))

    return recipients


def _render_submission_email_text(submission: MigrationIntakeSubmission) -> str:
    pairs = []
    for pair in submission.area_country_pairs or []:
        area = str((pair or {}).get("area", "")).strip()
        country = str((pair or {}).get("country", "")).strip()
        if area and country:
            pairs.append(f"{area} / {country}")

    lines = [
        "A new migration request has been submitted.",
        "",
        f"Migration Request ID: {submission.migration_request_id}",
        f"Requested Date: {submission.requested_date}",
        f"Requestor: {submission.requestor}",
        f"Status: {submission.status}",
        f"Project Name: {submission.project_name}",
        f"Migration Type: {submission.migration_type}",
        f"Migration Type Value: {submission.migration_type_value}",
        f"Region: {submission.region}",
        f"Function: {submission.function_name}",
        "",
        f"Areas: {_csv(submission.areas)}",
        f"Countries: {_csv(submission.countries)}",
        f"Area / Country Pairs: {_csv(pairs)}",
        f"Products: {_csv(submission.products)}",
        f"Language Dependencies: {_csv(submission.language_dependencies)}",
        "",
        f"Location Strategy Custom: {'Yes' if submission.location_strategy_custom else 'No'}",
        f"Default Location Strategies: {_csv(submission.default_location_strategies)}",
        f"Custom Location Strategies: {_csv(submission.custom_location_strategies)}",
        f"Custom Location Strategy Justification: {submission.custom_location_strategy_justification or '-'}",
        f"Custom Approval File: {submission.custom_approval_file_name or '-'}",
        f"Custom Approval File Size: {submission.custom_approval_file_size or '-'}",
        f"Custom Approval File Type: {submission.custom_approval_file_type or '-'}",
        "",
        f"Proposed Scope: {submission.proposed_scope}",
        f"Risks: {submission.risks or '-'}",
        "",
        f"FTE Number: {submission.fte_number}",
        f"JL2: {submission.jl2}",
        f"JL3: {submission.jl3}",
        f"JL4: {submission.jl4}",
        f"Job Level Total: {submission.job_level_total}",
    ]
    return "\n".join(lines)


def send_migration_intake_notification(
    submission: MigrationIntakeSubmission,
    *,
    signed_in_email: str = "",
) -> bool:
    recipients = resolve_notification_recipients(
        submission,
        signed_in_email=signed_in_email,
    )
    if not recipients:
        logger.warning(
            "Migration intake notification skipped for %s: no recipients configured.",
            submission.migration_request_id,
        )
        return False

    subject = f"Migration Request {submission.migration_request_id} - New Submission"
    body = _render_submission_email_text(submission)

    message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    message.send(fail_silently=False)
    return True
