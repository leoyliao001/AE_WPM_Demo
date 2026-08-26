"""Approval-stage email notifications for the Migration Approval workflow."""

import logging
from html import escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from api.models import MigrationIntakeSubmission
from api.permissions.approval_access import recipients_for_role

logger = logging.getLogger(__name__)

ROLE_LABELS = {
    "area_head": "Area Head",
    "pmo": "PMO",
    "bpm": "BPM",
    "fbp": "FBP",
    "wpm": "WPM",
    "elt": "ELT",
    "gsc_head": "GSC Head",
}


def _approval_url(submission: MigrationIntakeSubmission, role: str) -> str:
    base_url = getattr(settings, "DJANGO_PUBLIC_BASE_URL", "https://10.176.115.28").rstrip("/")
    if role in {"elt", "gsc_head"}:
        return f"{base_url}/approval-cycle/review/{submission.migration_request_id}/{role}"
    return f"{base_url}/approval-cycle?request={submission.migration_request_id}"


def send_next_stage_notification(submission: MigrationIntakeSubmission, role: str, rows=None) -> tuple[bool, list[str]]:
    """Email every approver configured for the next active approval role."""
    recipients = recipients_for_role(role, submission.function_name, submission.products, rows)
    if not recipients:
        logger.warning("No %s approver configured for %s", role, submission.migration_request_id)
        return False, []

    role_label = ROLE_LABELS[role]
    approval_url = _approval_url(submission, role)
    subject = f"Approval required: {submission.migration_request_id} - {role_label} review"
    text_body = "\n".join([
                f"Migration Approval Required - {role_label} Review",
        "",
                "Hello,",
                "",
                f"The migration request below is ready for your {role_label} review. Please review the submission and record your decision in the Migration Approval page.",
                "",
                f"Reference: {submission.migration_request_id}",
                f"Project Name: {submission.project_name}",
                f"Migration Type: {submission.migration_type}",
                f"Product(s): {', '.join(submission.products or []) or '-'}",
                f"Function: {submission.function_name}",
                f"Region / Area: {submission.region} / {', '.join(submission.areas or []) or '-'}",
                f"FTE in Scope: {submission.fte_number}",
                f"Proposed Scope: {submission.proposed_scope}",
        "",
                f"Open Migration Approval: {approval_url}",
                "",
                "This is an automated notification from the Workforce Planning and Migration system. Please do not reply to this email.",
    ])
    html_body = f"""
        <!DOCTYPE html>
        <html lang="en"><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,Helvetica,sans-serif;color:#263746;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:28px 0;"><tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;">
                    <tr><td style="background:#002b45;padding:24px 32px;">
                        <p style="margin:0 0 8px;color:#9fb7c8;font-size:11px;letter-spacing:1.3px;text-transform:uppercase;">WPM PULSE</p>
                        <h1 style="margin:0;color:#ffffff;font-size:21px;line-height:1.3;">Migration Approval Required</h1>
                    </td></tr>
                    <tr><td style="padding:28px 32px 12px;">
                        <p style="margin:0 0 16px;font-size:15px;">Hello,</p>
                        <p style="margin:0;font-size:14px;line-height:1.6;">The migration request below is ready for your <strong>{escape(role_label)}</strong> review. Please review the submission and record your decision in the Migration Approval page.</p>
                    </td></tr>
                    <tr><td style="padding:12px 32px 6px;">
                        <table width="100%" cellpadding="0" cellspacing="0" style="background:#edf5fc;border-left:4px solid #0073ab;"><tr><td style="padding:16px 18px;">
                            <p style="margin:0 0 4px;color:#5d6b76;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;">Reference</p>
                            <p style="margin:0;color:#002b45;font-size:20px;font-weight:700;">{escape(submission.migration_request_id)}</p>
                            <p style="margin:5px 0 0;color:#5d6b76;font-size:12px;">{escape(role_label)} approval stage</p>
                        </td></tr></table>
                    </td></tr>
                    <tr><td style="padding:14px 32px 0;"><h2 style="border-bottom:1px solid #dce3e8;color:#002b45;font-size:14px;margin:0;padding-bottom:9px;">Submission Summary</h2></td></tr>
                    <tr><td style="padding:4px 32px 18px;">
                        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
                            <tr><td style="padding:12px 4px;color:#5d6b76;width:40%;border-bottom:1px solid #edf0f2;">Project Name</td><td style="padding:12px 4px;font-weight:600;border-bottom:1px solid #edf0f2;">{escape(submission.project_name)}</td></tr>
                            <tr><td style="padding:12px 4px;color:#5d6b76;border-bottom:1px solid #edf0f2;">Migration Type</td><td style="padding:12px 4px;font-weight:600;border-bottom:1px solid #edf0f2;">{escape(submission.migration_type)}</td></tr>
                            <tr><td style="padding:12px 4px;color:#5d6b76;border-bottom:1px solid #edf0f2;">Product(s)</td><td style="padding:12px 4px;font-weight:600;border-bottom:1px solid #edf0f2;">{escape(', '.join(submission.products or []) or '-')}</td></tr>
                            <tr><td style="padding:12px 4px;color:#5d6b76;border-bottom:1px solid #edf0f2;">Function</td><td style="padding:12px 4px;font-weight:600;border-bottom:1px solid #edf0f2;">{escape(submission.function_name)}</td></tr>
                            <tr><td style="padding:12px 4px;color:#5d6b76;border-bottom:1px solid #edf0f2;">Region / Area</td><td style="padding:12px 4px;font-weight:600;border-bottom:1px solid #edf0f2;">{escape(submission.region)} / {escape(', '.join(submission.areas or []) or '-')}</td></tr>
                            <tr><td style="padding:12px 4px;color:#5d6b76;border-bottom:1px solid #edf0f2;">FTE in Scope</td><td style="padding:12px 4px;font-weight:600;border-bottom:1px solid #edf0f2;">{escape(submission.fte_number)}</td></tr>
                            <tr><td style="padding:12px 4px;color:#5d6b76;vertical-align:top;">Proposed Scope</td><td style="padding:12px 4px;font-weight:600;line-height:1.45;">{escape(submission.proposed_scope)}</td></tr>
                        </table>
                    </td></tr>
                    <tr><td style="padding:4px 32px 30px;"><a href="{escape(approval_url, quote=True)}" style="background:#0073ab;border-radius:3px;color:#ffffff;display:inline-block;font-size:14px;font-weight:700;padding:12px 18px;text-decoration:none;">Open Migration Approval</a><p style="color:#71808c;font-size:11px;line-height:1.5;margin:20px 0 0;">You received this email because you are configured as the {escape(role_label)} approver in Input for Approval. This is an automated notification; please do not reply directly.</p></td></tr>
                </table>
            </td></tr></table>
        </body></html>"""
    message = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, recipients)
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)
    logger.info("Approval notification sent for %s to %s: %s", submission.migration_request_id, role, recipients)
    return True, recipients


def send_return_notification(
        submission: MigrationIntakeSubmission,
        role: str,
        return_comment: str,
        rows=None,
) -> tuple[bool, list[str]]:
        """Notify the previous-stage owner that information was requested."""
        recipients = recipients_for_role(role, submission.function_name, submission.products, rows)
        if not recipients:
                logger.warning("No %s approver configured for returned request %s", role, submission.migration_request_id)
                return False, []

        role_label = ROLE_LABELS[role]
        approval_url = _approval_url(submission, role)
        subject = f"Information requested: {submission.migration_request_id} - {role_label} review reopened"
        text_body = "\n".join([
                f"Information requested for migration request {submission.migration_request_id}",
                "",
                f"Your {role_label} review has been reopened because a later approval stage requested further information.",
                f"Project: {submission.project_name}",
                f"Comment: {return_comment}",
                "",
                f"Open Migration Approval: {approval_url}",
        ])
        html_body = f"""
        <!DOCTYPE html><html lang="en"><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,Helvetica,sans-serif;color:#263746;">
            <table width="100%" cellpadding="0" cellspacing="0" style="padding:28px 0;"><tr><td align="center"><table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;">
                <tr><td style="background:#002b45;padding:24px 32px;"><p style="margin:0 0 8px;color:#9fb7c8;font-size:11px;letter-spacing:1.3px;text-transform:uppercase;">WPM PULSE</p><h1 style="margin:0;color:#ffffff;font-size:21px;">Information Requested</h1></td></tr>
                <tr><td style="padding:28px 32px;"><p style="margin:0 0 14px;font-size:14px;line-height:1.6;">Your <strong>{escape(role_label)}</strong> review has been reopened because a later approval stage requested further information.</p>
                    <table width="100%" cellpadding="0" cellspacing="0" style="background:#edf5fc;border-left:4px solid #0073ab;"><tr><td style="padding:16px 18px;"><p style="margin:0;color:#002b45;font-size:18px;font-weight:700;">{escape(submission.migration_request_id)}</p><p style="margin:5px 0 0;color:#5d6b76;font-size:12px;">{escape(submission.project_name)}</p></td></tr></table>
                    <p style="font-size:14px;line-height:1.6;"><strong>Requested information:</strong><br>{escape(return_comment)}</p>
                    <p style="margin:24px 0 0;"><a href="{escape(approval_url, quote=True)}" style="background:#0073ab;border-radius:3px;color:#ffffff;display:inline-block;font-size:14px;font-weight:700;padding:12px 18px;text-decoration:none;">Open Migration Approval</a></p>
                </td></tr>
            </table></td></tr></table>
        </body></html>"""
        message = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, recipients)
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)
        logger.info("Return notification sent for %s to %s: %s", submission.migration_request_id, role, recipients)
        return True, recipients