from functools import lru_cache
import logging

from django.conf import settings
from django.db import DatabaseError, connection, transaction
from django.utils import timezone
from django.utils.html import escape
import requests
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import GscSiteRequest, MigrationIntakeSubmission, StakeholderRegistration
from api.permissions.attributes_access import get_request_email, is_super_admin, normalize_email
from api.services.intake_options import all_location_strategy_options
from api.services.project_artefacts import migration_manager_emails, project_permissions

logger = logging.getLogger(__name__)

SITE_LIMIT = 128
COMMENT_LIMIT = 2000


@lru_cache(maxsize=1)
def gsc_request_table_available():
    try:
        return GscSiteRequest._meta.db_table in connection.introspection.table_names()
    except DatabaseError:
        return False


def _project(project_id):
    try:
        return MigrationIntakeSubmission.objects.get(pk=project_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return None


def _serialize(item, email):
    approvers = [
        normalize_email(value)
        for value in (item.approver_emails or [])
        if normalize_email(value)
    ]
    completed = item.status in {"approved", "rejected"}
    normalized_email = normalize_email(email)
    base_url = getattr(settings, "DJANGO_PUBLIC_BASE_URL", "https://wpmpulse.crb.apmoller.net").rstrip("/")
    return {
        "request_kind": "gsc_site",
        "gsc_request_id": item.pk,
        "migration_request_id": item.project.migration_request_id,
        "project_name": item.project.project_name,
        "requestor": item.requested_by,
        "region": item.project.region,
        "areas": item.project.areas or [],
        "requested_date": item.created_at.isoformat(),
        "status": item.status,
        "completed": completed,
        "step": 1 if not completed else 2,
        "totalSteps": 1,
        "currentRole": "migration_manager" if not completed else None,
        "myRoles": ["migration_manager"] if normalized_email in approvers else [],
        "actionable": normalized_email in approvers and item.status == "pending",
        "submittedByMe": normalized_email == normalize_email(item.requested_by),
        "approvedByMe": item.status == "approved"
        and normalized_email == normalize_email(item.decided_by),
        "handledByMe": normalized_email == normalize_email(item.decided_by),
        "gscSite": item.site,
        "gscRequestComment": item.request_comment,
        "gscStatus": item.status,
        "gscDecisionComment": item.decision_comment,
        "gscApprovers": approvers,
        "gscDecidedBy": item.decided_by,
        "gscDecidedAt": item.decided_at.isoformat() if item.decided_at else "",
        "gscReviewUrl": f"{base_url}/approval-cycle?gsc_request={item.pk}",
    }


def project_gsc_site_requests(project):
    if not gsc_request_table_available():
        return []
    return [
        {
            "id": item.pk,
            "site": item.site,
            "status": item.status,
            "requestComment": item.request_comment,
            "decisionComment": item.decision_comment,
            "approverEmails": item.approver_emails or [],
            "createdAt": item.created_at.isoformat(),
            "decidedAt": item.decided_at.isoformat() if item.decided_at else "",
        }
        for item in GscSiteRequest.objects.filter(project=project).order_by("-created_at", "id")
    ]


def approved_project_gsc_sites(project):
    if not gsc_request_table_available():
        return []
    return list(
        GscSiteRequest.objects.filter(project=project, status="approved")
        .order_by("site", "id")
        .values_list("site", flat=True)
    )


def list_gsc_site_requests(email, scope):
    if not gsc_request_table_available():
        return []
    items = GscSiteRequest.objects.select_related("project").all()
    normalized_email = normalize_email(email)
    if scope != "all" and not is_super_admin(email):
        items = [
            item
            for item in items
            if normalize_email(item.requested_by) == normalized_email
            or normalized_email in (normalize_email(value) for value in (item.approver_emails or []))
            or normalize_email(item.decided_by) == normalized_email
        ]
    return [_serialize(item, email) for item in items]


def _send_email(recipients, subject, text_body, html_body):
    api_key = getattr(settings, "SENDGRID_API_KEY", "")
    if not api_key:
        raise RuntimeError("The SendGrid API key is not configured.")
    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "personalizations": [
                {"to": [{"email": recipient}]} for recipient in recipients
            ],
            "from": {"email": settings.DEFAULT_FROM_EMAIL},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": text_body},
                {"type": "text/html", "value": html_body},
            ],
        },
        verify=getattr(settings, "_ca_bundle", True),
        timeout=30,
    )
    if response.status_code != 202:
        raise RuntimeError(
            f"SendGrid API returned {response.status_code}: {response.text[:500]}"
        )


def _send_request_email(item):
    _send_request_batch_email([item])


def _send_request_batch_email(items):
    item = items[0]
    base_url = getattr(settings, "DJANGO_PUBLIC_BASE_URL", "https://wpmpulse.crb.apmoller.net").rstrip("/")
    review_links = [
        (entry.site, f"{base_url}/approval-cycle?gsc_request={entry.pk}")
        for entry in items
    ]
    subject = f"GSC Site approval requested for {item.project.migration_request_id}"
    site_names = [entry.site for entry in items]
    site_text = ", ".join(site_names)
    site_rows = "".join(
        "<tr>"
        "<th align='left' style='padding:8px 10px;border:1px solid #dce5e8;'>Requested GSC Site</th>"
        f"<td style='padding:8px 10px;border:1px solid #dce5e8;'>{escape(site)}</td>"
        "</tr>"
        for site in site_names
    )
    review_rows = "".join(
        "<tr>"
        "<td style='padding:10px 0;'>"
        f"<strong>{escape(site)}</strong><br>"
        f"<a href='{escape(url)}' style='color:#0073ab;text-decoration:none;'>Open approval for {escape(site)}</a>"
        "</td>"
        "</tr>"
        for site, url in review_links
    )
    text_body = "\n".join([
        "A project-specific GSC Site request requires Migration Manager review.",
        "",
        f"Project: {item.project.project_name}",
        f"Migration Request ID: {item.project.migration_request_id}",
        f"Requested GSC Sites: {site_text}",
        f"Requested by: {item.requested_by}",
        f"Reason: {item.request_comment}",
        "",
        *[f"{site}: {url}" for site, url in review_links],
        "",
        "The site will become available on the project Resources page only after approval.",
    ])
    html_body = f"""
        <div style="font-family:Segoe UI,Arial,sans-serif;color:#173747;background:#f5f8fa;padding:24px;">
          <div style="max-width:640px;margin:auto;background:#fff;border:1px solid #dce5e8;border-top:4px solid #42b0d5;border-radius:8px;">
            <div style="padding:20px 24px;">
              <h2 style="margin:0 0 8px;font-size:20px;color:#173747;">GSC Site approval required</h2>
              <p style="margin:0 0 18px;font-size:14px;color:#526d7f;">A project-specific GSC Site request requires Migration Manager review.</p>
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
                <tr><th align="left" style="width:180px;padding:8px 10px;border:1px solid #dce5e8;">Project</th><td style="padding:8px 10px;border:1px solid #dce5e8;">{escape(item.project.project_name)}</td></tr>
                <tr><th align="left" style="padding:8px 10px;border:1px solid #dce5e8;">Migration Request ID</th><td style="padding:8px 10px;border:1px solid #dce5e8;">{escape(item.project.migration_request_id)}</td></tr>
                {site_rows}
                <tr><th align="left" style="padding:8px 10px;border:1px solid #dce5e8;">Requested by</th><td style="padding:8px 10px;border:1px solid #dce5e8;">{escape(item.requested_by)}</td></tr>
                <tr><th align="left" style="padding:8px 10px;border:1px solid #dce5e8;">Reason</th><td style="padding:8px 10px;border:1px solid #dce5e8;">{escape(item.request_comment)}</td></tr>
              </table>
              <table cellpadding="0" cellspacing="0" style="margin-top:18px;font-size:13px;">{review_rows}</table>
              <p style="margin:16px 0 0;font-size:12px;color:#526d7f;">The site will become available on the project Resources page only after approval.</p>
            </div>
          </div>
        </div>
    """
    _send_email(item.approver_emails, subject, text_body, html_body)


def _send_decision_email(item):
    base_url = getattr(settings, "DJANGO_PUBLIC_BASE_URL", "https://wpmpulse.crb.apmoller.net").rstrip("/")
    review_url = f"{base_url}/approval-cycle?gsc_request={item.pk}"
    decision = "approved" if item.status == "approved" else "rejected"
    status_color = "#176345" if item.status == "approved" else "#a3332c"
    status_label = "Approved" if item.status == "approved" else "Rejected"
    subject = f"GSC Site request {decision} for {item.project.migration_request_id}"
    text_body = "\n".join([
        f"Your request to add {item.site} has been {decision}.",
        "",
        f"Project: {item.project.project_name}",
        f"Migration Request ID: {item.project.migration_request_id}",
        f"Migration Manager comment: {item.decision_comment or 'No additional comment.'}",
        f"Reviewed by: {item.decided_by}",
        "",
        f"Open the request in Approval Cycle: {review_url}",
    ])
    html_body = f"""
        <div style="font-family:Segoe UI,Arial,sans-serif;color:#173747;background:#f5f8fa;padding:24px;">
          <div style="max-width:640px;margin:auto;background:#fff;border:1px solid #dce5e8;border-top:4px solid #42b0d5;border-radius:8px;">
            <div style="padding:20px 24px;">
              <h2 style="margin:0 0 8px;font-size:20px;color:{status_color};">GSC Site request {status_label}</h2>
              <p style="margin:0 0 18px;font-size:14px;color:#526d7f;">Your request to add <strong>{escape(item.site)}</strong> has been {decision}.</p>
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
                <tr><th align="left" style="width:180px;padding:8px 10px;border:1px solid #dce5e8;">Project</th><td style="padding:8px 10px;border:1px solid #dce5e8;">{escape(item.project.project_name)}</td></tr>
                <tr><th align="left" style="padding:8px 10px;border:1px solid #dce5e8;">Migration Request ID</th><td style="padding:8px 10px;border:1px solid #dce5e8;">{escape(item.project.migration_request_id)}</td></tr>
                <tr><th align="left" style="padding:8px 10px;border:1px solid #dce5e8;">Migration Manager comment</th><td style="padding:8px 10px;border:1px solid #dce5e8;">{escape(item.decision_comment or 'No additional comment.')}</td></tr>
                <tr><th align="left" style="padding:8px 10px;border:1px solid #dce5e8;">Reviewed by</th><td style="padding:8px 10px;border:1px solid #dce5e8;">{escape(item.decided_by)}</td></tr>
              </table>
              <p style="margin:18px 0 0;"><a href="{escape(review_url)}" style="display:inline-block;background:#0073ab;color:#fff;border-radius:5px;padding:9px 14px;text-decoration:none;font-size:13px;">Open Approval Cycle</a></p>
            </div>
          </div>
        </div>
    """
    _send_email([item.requested_by], subject, text_body, html_body)


@api_view(["POST"])
def submit_gsc_site_request(request, project_id):
    project = _project(project_id)
    if project is None:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED)
    if not project_permissions(project, email, "resources")["edit"]:
        return Response({"error": "You do not have permission to request a GSC Site for this project."}, status=status.HTTP_403_FORBIDDEN)
    if not gsc_request_table_available():
        return Response(
            {"error": "GSC Site requests are temporarily unavailable until the database migration is applied."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    payload = request.data if isinstance(request.data, dict) else {}
    raw_sites = payload.get("sites")
    if raw_sites is None and payload.get("site"):
        raw_sites = [payload.get("site")]
    if not isinstance(raw_sites, list) or not raw_sites:
        return Response({"error": "Select at least one GSC Site."}, status=status.HTTP_400_BAD_REQUEST)
    sites = list(dict.fromkeys(str(value or "").strip() for value in raw_sites))
    comment = str(payload.get("request_comment") or "").strip()
    allowed_sites = set(all_location_strategy_options())
    if any(not site or len(site) > SITE_LIMIT for site in sites):
        return Response({"error": f"Each GSC Site is required and must not exceed {SITE_LIMIT} characters."}, status=status.HTTP_400_BAD_REQUEST)
    if any(site not in allowed_sites for site in sites):
        return Response({"error": "Choose GSC Sites from the Migration Intake Strategic Location options."}, status=status.HTTP_400_BAD_REQUEST)
    if not comment or len(comment) > COMMENT_LIMIT:
        return Response({"error": f"A reason is required and must not exceed {COMMENT_LIMIT} characters."}, status=status.HTTP_400_BAD_REQUEST)

    existing_sites = {
        value.casefold()
        for value in (project.default_location_strategies or [])
        + (project.custom_location_strategies or [])
    }
    already_available = [site for site in sites if site.casefold() in existing_sites]
    if already_available:
        return Response({"error": f"{', '.join(already_available)} is already available for the project."}, status=status.HTTP_409_CONFLICT)
    existing_requests = set(
        value.casefold()
        for value in GscSiteRequest.objects.filter(
            project=project,
            site__in=sites,
            status__in=["pending", "approved"],
        ).values_list("site", flat=True)
    )
    duplicates = [site for site in sites if site.casefold() in existing_requests]
    if duplicates:
        return Response({"error": f"A pending or approved request already exists for {', '.join(duplicates)}."}, status=status.HTTP_409_CONFLICT)

    registration = StakeholderRegistration.objects.filter(project=project).first()
    assignment = (registration.assignments or {}).get("migration_manager", {}) if registration else {}
    if not isinstance(assignment, dict) or not assignment.get("lockedAt"):
        return Response(
            {"error": "Assign and lock a Migration Manager in this project's Stakeholder Registration before submitting."},
            status=status.HTTP_409_CONFLICT,
        )
    approvers = migration_manager_emails(project, registration)
    if not approvers:
        return Response(
            {"error": "Assign and lock a Migration Manager in this project's Stakeholder Registration before submitting."},
            status=status.HTTP_409_CONFLICT,
        )

    with transaction.atomic():
        items = [
            GscSiteRequest.objects.create(
                project=project,
                site=site,
                requested_by=email,
                approver_emails=approvers,
                request_comment=comment,
            )
            for site in sites
        ]
        try:
            _send_request_batch_email(items)
        except Exception as exc:
            transaction.set_rollback(True)
            return Response({"error": f"Unable to send the Migration Manager approval email: {exc}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    rows = [_serialize(item, email) for item in items]
    return Response(
        {"count": len(rows), "rows": rows, **rows[0]},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def decide_gsc_site_request(request, request_id):
    email = normalize_email(get_request_email(request))
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED)
    if not gsc_request_table_available():
        return Response(
            {"error": "GSC Site requests are temporarily unavailable until the database migration is applied."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    with transaction.atomic():
        try:
            item = (
                GscSiteRequest.objects.select_for_update()
                .select_related("project")
                .get(pk=request_id)
            )
        except GscSiteRequest.DoesNotExist:
            return Response({"error": "GSC Site request not found."}, status=status.HTTP_404_NOT_FOUND)
        approvers = [normalize_email(value) for value in (item.approver_emails or [])]
        if email not in approvers and not is_super_admin(email):
            return Response({"error": "You are not authorised to decide this GSC Site request."}, status=status.HTTP_403_FORBIDDEN)
        if item.status != "pending":
            return Response({"error": "This GSC Site request has already been decided."}, status=status.HTTP_409_CONFLICT)

        payload = request.data if isinstance(request.data, dict) else {}
        action = str(payload.get("action") or "").strip().lower()
        comment = str(payload.get("comment") or "").strip()
        if action not in {"approved", "rejected"}:
            return Response({"error": "Choose approved or rejected."}, status=status.HTTP_400_BAD_REQUEST)
        if action == "rejected" and not comment:
            return Response({"error": "A comment is required when rejecting a request."}, status=status.HTTP_400_BAD_REQUEST)
        if len(comment) > COMMENT_LIMIT:
            return Response({"error": f"The comment exceeds {COMMENT_LIMIT} characters."}, status=status.HTTP_400_BAD_REQUEST)

        item.status = action
        item.decision_comment = comment
        item.decided_by = email
        item.decided_at = timezone.now()
        item.save(update_fields=[
            "status", "decision_comment", "decided_by", "decided_at", "updated_at"
        ])
        row = _serialize(item, email)

    notification_sent = True
    try:
        _send_decision_email(item)
    except Exception as exc:
        notification_sent = False
        logger.exception("GSC Site decision notification failed for request %s: %s", item.pk, exc)
    return Response({"status": "success", "row": row, "notification_sent": notification_sent})
