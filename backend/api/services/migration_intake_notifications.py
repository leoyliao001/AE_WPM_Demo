import logging
import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q

from api.models import MigrationIntakeSubmission, ProductOwnership

logger = logging.getLogger(__name__)

# Allow proper emails AND @localhost for local-dev mock SSO.
EMAIL_RE = re.compile(r"[^@\s,;]+@(?:[^@\s,;]+\.[^@\s,;]+|localhost)", re.I)


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

    def add_one(value: str):
        email = _normalize_email(value)
        if not email or email in seen:
            return
        seen.add(email)
        recipients.append(email)

    def add_many(values):
        for value in values:
            add_one(value)

    # 1. Static fallback list from environment.
    add_many(getattr(settings, "MIGRATION_INTAKE_NOTIFY_TO", []) or [])

    # 2. Current signed-in user (from JWT / X-User-Email header) — use directly
    #    because it was already validated by get_request_email().
    if signed_in_email:
        add_one(signed_in_email)

    # 3. Requestor stored on submission (email sent from frontend).
    for email in _extract_emails(submission.requestor):
        add_one(email)
    # If requestor is not email-shaped (e.g. a display name), fall back to signed-in.
    if submission.requestor and not _extract_emails(submission.requestor) and signed_in_email:
        add_one(signed_in_email)

    # 4. Migration managers from ProductOwnership, matched by region.
    add_many(_manager_emails_for_submission(submission))

    logger.info(
        "Migration intake notification recipients for %s: %s",
        submission.migration_request_id,
        recipients,
    )
    return recipients


def _esc(value) -> str:
    """HTML-escape a value for safe embedding."""
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _row(label: str, value: str) -> str:
    if not value or value == "-":
        return ""
    return f"""
        <tr>
          <td style="padding:10px 16px;color:#6b7a8d;font-size:14px;width:40%;border-bottom:1px solid #e8ecf0;vertical-align:top;">{_esc(label)}</td>
          <td style="padding:10px 16px;color:#1a2b3c;font-size:14px;font-weight:600;border-bottom:1px solid #e8ecf0;vertical-align:top;">{_esc(value)}</td>
        </tr>"""


def _render_submission_email_html(submission: MigrationIntakeSubmission) -> str:
    pairs = []
    for pair in submission.area_country_pairs or []:
        area = str((pair or {}).get("area", "")).strip()
        country = str((pair or {}).get("country", "")).strip()
        if area and country:
            pairs.append(f"{area} / {country}")

    location_strategy = (
        _csv(submission.custom_location_strategies)
        if submission.location_strategy_custom
        else _csv(submission.default_location_strategies)
    )

    # Derive a display name from the requestor email (part before @)
    requestor_display = submission.requestor or "there"
    if "@" in requestor_display:
        requestor_display = requestor_display.split("@")[0].replace(".", " ").title()

    summary_rows = "".join([
        _row("Project Name", submission.project_name),
        _row("Migration Type", submission.migration_type),
        _row("Region", submission.region),
        _row("Function", submission.function_name),
        _row("Areas", _csv(submission.areas)),
        _row("Countries", _csv(submission.countries)),
        _row("Area / Country Pairs", _csv(pairs)),
        _row("Products", _csv(submission.products)),
        _row("Language Dependencies", _csv(submission.language_dependencies)),
        _row("Location Strategy", location_strategy),
        _row("Custom Strategy Justification", submission.custom_location_strategy_justification or ""),
        _row("Proposed Scope", submission.proposed_scope),
        _row("Risks", submission.risks or ""),
        _row("FTE Number", submission.fte_number),
        _row("JL2 / JL3 / JL4",
             f"{submission.jl2} / {submission.jl3} / {submission.jl4}"
             if any([submission.jl2, submission.jl3, submission.jl4]) else ""),
        _row("Job Level Total", str(submission.job_level_total) if submission.job_level_total else ""),
        _row("Status", submission.status.title() if submission.status else ""),
        _row("Requestor", submission.requestor),
    ])

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:4px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:#00243d;padding:32px 40px;">
            <p style="margin:0 0 8px 0;color:#a8bfd4;font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;">WPM</p>
            <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:700;line-height:1.2;">Migration Request Submitted</h1>
          </td>
        </tr>

        <!-- Greeting -->
        <tr>
          <td style="padding:32px 40px 16px;">
            <p style="margin:0 0 16px;color:#1a2b3c;font-size:16px;">Hi <strong>{_esc(requestor_display)}</strong>,</p>
            <p style="margin:0;color:#4a5568;font-size:15px;line-height:1.6;">
              Your migration request has been successfully submitted and is now pending review
              by the Migration Management team. A Migration Manager will evaluate your submission
              and reach out to you shortly.
            </p>
          </td>
        </tr>

        <!-- Reference box -->
        <tr>
          <td style="padding:16px 40px 24px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#e8f0fa;border-left:4px solid #0073ab;border-radius:2px;">
              <tr>
                <td style="padding:20px 24px;">
                  <p style="margin:0 0 4px;color:#6b7a8d;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;">Reference</p>
                  <p style="margin:0 0 6px;color:#00243d;font-size:22px;font-weight:700;">{_esc(submission.migration_request_id)}</p>
                  <p style="margin:0;color:#6b7a8d;font-size:13px;">Submitted on {_esc(submission.requested_date)}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Submission Summary -->
        <tr>
          <td style="padding:0 40px 8px;">
            <p style="margin:0 0 12px;color:#00243d;font-size:16px;font-weight:700;border-bottom:2px solid #e8ecf0;padding-bottom:8px;">Submission Summary</p>
            <table width="100%" cellpadding="0" cellspacing="0">
              {summary_rows}
            </table>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:24px 40px 32px;">
            <p style="margin:0;color:#8a9ab0;font-size:12px;line-height:1.6;">
              This is an automated notification from the Workforce Planning &amp; Migration system.
              Please do not reply directly to this email.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _render_submission_email_text(submission: MigrationIntakeSubmission) -> str:
    """Plain-text fallback for email clients that don't render HTML."""
    pairs = []
    for pair in submission.area_country_pairs or []:
        area = str((pair or {}).get("area", "")).strip()
        country = str((pair or {}).get("country", "")).strip()
        if area and country:
            pairs.append(f"{area} / {country}")

    lines = [
        "Migration Request Submitted",
        "=" * 40,
        "",
        f"Migration Request ID : {submission.migration_request_id}",
        f"Submitted On         : {submission.requested_date}",
        f"Requestor            : {submission.requestor}",
        f"Status               : {submission.status}",
        "",
        "SUBMISSION SUMMARY",
        "-" * 40,
        f"Project Name         : {submission.project_name}",
        f"Migration Type       : {submission.migration_type}",
        f"Region               : {submission.region}",
        f"Function             : {submission.function_name}",
        f"Areas                : {_csv(submission.areas)}",
        f"Countries            : {_csv(submission.countries)}",
        f"Area / Country Pairs : {_csv(pairs)}",
        f"Products             : {_csv(submission.products)}",
        f"Language Dependencies: {_csv(submission.language_dependencies)}",
        f"Location Strategy    : {_csv(submission.custom_location_strategies if submission.location_strategy_custom else submission.default_location_strategies)}",
        f"Proposed Scope       : {submission.proposed_scope}",
        f"Risks                : {submission.risks or '-'}",
        f"FTE Number           : {submission.fte_number}",
        f"JL2 / JL3 / JL4     : {submission.jl2} / {submission.jl3} / {submission.jl4}",
        f"Job Level Total      : {submission.job_level_total}",
    ]
    return "\n".join(lines)


def send_migration_intake_notification(
    submission: MigrationIntakeSubmission,
    *,
    signed_in_email: str = "",
) -> tuple[bool, list[str]]:
    """Send notification email. Returns (sent: bool, recipients: list[str])."""
    recipients = resolve_notification_recipients(
        submission,
        signed_in_email=signed_in_email,
    )
    if not recipients:
        logger.warning(
            "Migration intake notification skipped for %s: no recipients configured.",
            submission.migration_request_id,
        )
        return False, []

    subject = f"Migration Request {submission.migration_request_id} - New Submission"
    text_body = _render_submission_email_text(submission)
    html_body = _render_submission_email_html(submission)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)
    logger.info(
        "Migration intake notification sent for %s to: %s",
        submission.migration_request_id,
        recipients,
    )
    return True, recipients
