from __future__ import annotations

import logging
import re
from functools import lru_cache
from uuid import UUID, uuid4

from django.conf import settings
from django.db import DatabaseError, connection, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.html import escape
import requests
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import FpoCatalogueRequest, ServiceCatalogue, StakeholderRegistration
from api.permissions.attributes_access import get_request_email, is_super_admin, normalize_email
from api.views.stakeholder_registration import (
    _assigned_role_emails,
    _authorize,
    _get_project,
)

logger = logging.getLogger(__name__)

FIELD_LIMITS = {"l1": 128, "l2": 128, "l3": 128, "l4": 255}
REQUEST_COMMENT_LIMIT = 2000


@lru_cache(maxsize=1)
def _request_table_available() -> bool:
    try:
        return FpoCatalogueRequest._meta.db_table in connection.introspection.table_names()
    except DatabaseError:
        logger.exception("Unable to check FPO catalogue request table availability")
        return False


def _catalogue_product(value: str) -> str:
    return re.sub(r"^General\s+", "", value.strip(), flags=re.IGNORECASE).strip()


def _serialize_request(item: FpoCatalogueRequest, email: str, batch_count: int = 1) -> dict:
    approver = normalize_email(item.approver_email) == normalize_email(email)
    requester = normalize_email(item.requested_by) == normalize_email(email)
    decided_by_me = normalize_email(item.decided_by) == normalize_email(email)
    completed = item.status in {"approved", "rejected"}
    return {
        "request_kind": "fpo_catalogue",
        "fpo_request_id": item.pk,
        "fpo_batch_id": str(item.batch_id) if item.batch_id else "",
        "fpo_batch_count": batch_count,
        "migration_request_id": item.project.migration_request_id,
        "project_name": item.project.project_name,
        "migration_type": "Service Catalogue request",
        "migration_type_value": "fpo_catalogue",
        "requestor": item.requested_by,
        "region": item.project.region,
        "areas": item.project.areas or [],
        "countries": item.project.countries or [],
        "function_name": item.project.function_name,
        "products": [item.product],
        "proposed_scope": " / ".join((item.l1, item.l2, item.l3, item.l4)),
        "fte_number": "0",
        "requested_date": item.created_at.isoformat(),
        "status": item.status,
        "step": 1 if not completed else 2,
        "totalSteps": 1,
        "budgetStatus": "pending",
        "beyondBudget": False,
        "currentRole": "fpo" if not completed else None,
        "parallel": {"elt": "pending", "gscHead": "pending"},
        "completed": completed,
        "businessCaseStatus": None,
        "businessCaseBlocked": False,
        "myRoles": ["fpo"] if approver else [],
        "actionable": approver and item.status == "pending",
        "submittedByMe": requester,
        "approvedByMe": item.status == "approved" and decided_by_me,
        "handledByMe": decided_by_me,
        "fpoProduct": item.product,
        "fpoRequestComment": item.request_comment,
        "fpoL1": item.l1,
        "fpoL2": item.l2,
        "fpoL3": item.l3,
        "fpoL4": item.l4,
        "fpoStatus": item.status,
        "fpoDecisionComment": item.decision_comment,
        "fpoApprover": item.approver_email,
        "fpoDecidedBy": item.decided_by,
        "fpoDecidedAt": item.decided_at.isoformat() if item.decided_at else "",
    }


def list_fpo_catalogue_requests(email: str, scope: str) -> list[dict]:
    if not _request_table_available():
        return []
    requests = FpoCatalogueRequest.objects.select_related("project").all()
    if scope != "all":
        requests = requests.filter(
            Q(requested_by__iexact=email)
            | Q(approver_email__iexact=email)
            | Q(decided_by__iexact=email)
        )
    items = list(requests)
    batch_counts = {}
    for item in items:
        if item.batch_id:
            batch_counts[item.batch_id] = batch_counts.get(item.batch_id, 0) + 1
    return [
        _serialize_request(item, email, batch_counts.get(item.batch_id, 1))
        for item in items
    ]


def catalogue_request_reminders(project) -> list[dict]:
    if not _request_table_available():
        return []
    return [
        {
            "id": item.pk,
            "batch_id": str(item.batch_id) if item.batch_id else "",
            "product": item.product,
            "l1": item.l1,
            "l2": item.l2,
            "l3": item.l3,
            "l4": item.l4,
            "status": item.status,
            "decision_comment": item.decision_comment,
            "request_comment": item.request_comment,
            "created_at": item.created_at.isoformat(),
        }
        for item in FpoCatalogueRequest.objects.filter(
            project=project, catalogue_updated_at__isnull=True
        ).order_by("-created_at", "id")
    ]


def _send_request_email(item: FpoCatalogueRequest) -> None:
    _send_request_batch_email([item])


def _send_request_batch_email(items: list[FpoCatalogueRequest]) -> None:
    item = items[0]
    base_url = getattr(settings, "DJANGO_PUBLIC_BASE_URL", "").rstrip("/")
    review_url = f"{base_url}/approval-cycle?fpo_batch={item.batch_id}" if item.batch_id else f"{base_url}/approval-cycle?fpo_request={item.pk}"
    count = len(items)
    entries_text = "\n\n".join(
        "\n".join([
            f"Entry {index}", f"Product: {entry.product}", f"L1: {entry.l1}",
            f"L2: {entry.l2}", f"L3: {entry.l3}", f"L4: {entry.l4}",
        ])
        for index, entry in enumerate(items, start=1)
    )
    entries_html = "".join(
        "<tr><th colspan='2' align='left'>Entry {}</th></tr>".format(index)
        + "".join(
            f"<tr><th align='left'>{label}</th><td>{escape(value)}</td></tr>"
            for label, value in (("Product", entry.product), ("L1", entry.l1), ("L2", entry.l2), ("L3", entry.l3), ("L4", entry.l4))
        )
        for index, entry in enumerate(items, start=1)
    )
    subject = f"FPO approval requested: {count} Service Catalogue entr{'y' if count == 1 else 'ies'} for {item.project.migration_request_id}"
    text_body = "\n".join([
        f"{count} Service Catalogue entr{'y' if count == 1 else 'ies'} require FPO review.",
        "",
        "This request was created because the requester selected 'Not in Service Catalog' in Opportunity Assessment.",
        f"Project: {item.project.project_name}",
        f"Migration Request ID: {item.project.migration_request_id}",
        "",
        entries_text,
        f"Requested by: {item.requested_by}",
        f"Reason: {item.request_comment}",
        "",
        f"Review this request in Approval Cycle: {review_url}",
        "The entries will be added to Service Catalogue only after approval.",
    ])
    html_body = f"""
        <p>{count} Service Catalogue entr{'y' if count == 1 else 'ies'} require FPO review.</p>
        <p>This request was created because the requester selected <strong>Not in Service Catalog</strong> in Opportunity Assessment.</p>
        <table>
            <tr><th align="left">Project</th><td>{escape(item.project.project_name)}</td></tr>
            <tr><th align="left">Migration Request ID</th><td>{escape(item.project.migration_request_id)}</td></tr>
            {entries_html}
            <tr><th align="left">Requested by</th><td>{escape(item.requested_by)}</td></tr>
            <tr><th align="left">Reason</th><td>{escape(item.request_comment)}</td></tr>
        </table>
        <p><a href="{escape(review_url)}">Open Approval Cycle to review this request</a></p>
        <p>The entries will be added to Service Catalogue only after approval.</p>
    """
    _send_sendgrid_email(item.approver_email, subject, text_body, html_body)


def _send_sendgrid_email(to_email: str, subject: str, text_body: str, html_body: str) -> None:
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
            "personalizations": [{"to": [{"email": to_email}]}],
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


def _send_decision_email(item: FpoCatalogueRequest) -> None:
    _send_decision_batch_email([item])


def _send_decision_batch_email(items: list[FpoCatalogueRequest]) -> None:
    item = items[0]
    base_url = getattr(settings, "DJANGO_PUBLIC_BASE_URL", "").rstrip("/")
    review_url = f"{base_url}/approval-cycle?fpo_batch={item.batch_id}" if item.batch_id else f"{base_url}/approval-cycle?fpo_request={item.pk}"
    decision = "approved" if item.status == "approved" else "rejected"
    count = len(items)
    subject = f"FPO request {decision}: {count} Service Catalogue entr{'y' if count == 1 else 'ies'} for {item.project.migration_request_id}"
    entries_text = "\n\n".join(
        "\n".join([
            f"Entry {index}", f"Product: {entry.product}", f"L1: {entry.l1}",
            f"L2: {entry.l2}", f"L3: {entry.l3}", f"L4: {entry.l4}",
        ])
        for index, entry in enumerate(items, start=1)
    )
    entries_html = "".join(
        "<tr><th colspan='2' align='left'>Entry {}</th></tr>".format(index)
        + "".join(
            f"<tr><th align='left'>{label}</th><td>{escape(value)}</td></tr>"
            for label, value in (("Product", entry.product), ("L1", entry.l1), ("L2", entry.l2), ("L3", entry.l3), ("L4", entry.l4))
        )
        for index, entry in enumerate(items, start=1)
    )
    text_body = "\n".join([
        f"Your FPO Service Catalogue request for {count} entr{'y' if count == 1 else 'ies'} has been {decision}.",
        "",
        f"Project: {item.project.project_name}",
        f"Migration Request ID: {item.project.migration_request_id}",
        "",
        entries_text,
        f"Your reason: {item.request_comment}",
        f"FPO comment: {item.decision_comment or 'No additional comment.'}",
        f"Reviewed by: {item.decided_by}",
        "",
        f"Open the request in Approval Cycle: {review_url}",
    ])
    html_body = f"""
        <p>Your FPO Service Catalogue request for {count} entr{'y' if count == 1 else 'ies'} has been <strong>{escape(decision)}</strong>.</p>
        <table>
            <tr><th align="left">Project</th><td>{escape(item.project.project_name)}</td></tr>
            <tr><th align="left">Migration Request ID</th><td>{escape(item.project.migration_request_id)}</td></tr>
            {entries_html}
            <tr><th align="left">Your reason</th><td>{escape(item.request_comment)}</td></tr>
            <tr><th align="left">FPO comment</th><td>{escape(item.decision_comment or 'No additional comment.')}</td></tr>
            <tr><th align="left">Reviewed by</th><td>{escape(item.decided_by)}</td></tr>
        </table>
        <p><a href="{escape(review_url)}">Open the request in Approval Cycle</a></p>
    """
    _send_sendgrid_email(item.requested_by, subject, text_body, html_body)


def _insert_service_catalogue_entry(item: FpoCatalogueRequest) -> None:
    now = timezone.now()
    values = {
        "catalogue": "Service Catalogue",
        "product": item.product,
        "l1": item.l1,
        "l2": item.l2,
        "l3": item.l3,
        "l4": item.l4,
        "current_ownership": "",
        "customer": "",
        "direction": "",
        "average_handle_time": "",
        "task_name": item.l4,
        "created_at": now,
        "updated_at": now,
    }
    table = ServiceCatalogue._meta.db_table
    with connection.cursor() as cursor:
        columns = {
            column.name.casefold(): column.name
            for column in connection.introspection.get_table_description(cursor, table)
        }
        insert_values = {
            columns[name]: value for name, value in values.items() if name in columns
        }
        quote_name = connection.ops.quote_name
        column_sql = ", ".join(quote_name(name) for name in insert_values)
        placeholders = ", ".join(["%s"] * len(insert_values))
        cursor.execute(
            f"INSERT INTO {quote_name(table)} ({column_sql}) VALUES ({placeholders})",
            list(insert_values.values()),
        )


@api_view(["POST"])
def submit_fpo_catalogue_request(request, project_id: int):
    project = _get_project(project_id)
    if project is None:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    email, error = _authorize(request, project)
    if error:
        return error
    if not _request_table_available():
        return Response(
            {"error": "FPO catalogue requests are temporarily unavailable until the database migration is applied."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    payload = request.data if isinstance(request.data, dict) else {}
    product = _catalogue_product(str(payload.get("product") or ""))
    allowed_products = {_catalogue_product(str(value)) for value in (project.products or [])}
    if not product or product.casefold() not in {value.casefold() for value in allowed_products if value}:
        return Response({"error": "Choose a product from this project's intake."}, status=status.HTTP_400_BAD_REQUEST)

    raw_entries = payload.get("entries", [payload])
    if not isinstance(raw_entries, list) or not raw_entries or len(raw_entries) > 100:
        return Response({"error": "Submit between 1 and 100 catalogue entries."}, status=status.HTTP_400_BAD_REQUEST)

    entries = []
    seen = set()
    for index, raw_entry in enumerate(raw_entries, start=1):
        if not isinstance(raw_entry, dict):
            return Response({"error": f"Entry {index} must be an object."}, status=status.HTTP_400_BAD_REQUEST)
        values = {}
        for field, limit in FIELD_LIMITS.items():
            value = str(raw_entry.get(field) or "").strip()
            if not value:
                return Response({"error": f"Entry {index}: {field.upper()} is required."}, status=status.HTTP_400_BAD_REQUEST)
            if len(value) > limit:
                return Response({"error": f"Entry {index}: {field.upper()} exceeds {limit} characters."}, status=status.HTTP_400_BAD_REQUEST)
            values[field] = value

        key = tuple([product, *(values[field] for field in FIELD_LIMITS)])
        normalized_key = tuple(value.casefold() for value in key)
        if normalized_key in seen:
            return Response({"error": f"Entry {index} duplicates another entry in this batch."}, status=status.HTTP_400_BAD_REQUEST)
        seen.add(normalized_key)
        exists = ServiceCatalogue.objects.filter(
            product__iexact=product,
            l1__iexact=values["l1"],
            l2__iexact=values["l2"],
            l3__iexact=values["l3"],
            l4__iexact=values["l4"],
        ).exists()
        if exists:
            return Response({"error": f"Entry {index} already exists in Service Catalogue."}, status=status.HTTP_409_CONFLICT)
        entries.append(values)

    request_comment = str(payload.get("request_comment") or "").strip()
    if not request_comment:
        return Response({"error": "A reason for the FPO request is required."}, status=status.HTTP_400_BAD_REQUEST)
    if len(request_comment) > REQUEST_COMMENT_LIMIT:
        return Response({"error": f"The reason exceeds {REQUEST_COMMENT_LIMIT} characters."}, status=status.HTTP_400_BAD_REQUEST)

    registration = StakeholderRegistration.objects.filter(project=project).only(
        "team_members", "assignments"
    ).first()
    approver_emails = _assigned_role_emails(registration, "fpo")
    if len(approver_emails) != 1:
        return Response(
            {"error": "Assign exactly one FPO in this project's Stakeholder Registration before submitting."},
            status=status.HTTP_409_CONFLICT,
        )
    approver_email = approver_emails[0]
    batch_id = uuid4()
    with transaction.atomic():
        items = [
            FpoCatalogueRequest.objects.create(
                project=project,
                batch_id=batch_id,
                product=product,
                requested_by=email,
                approver_email=approver_email,
                request_comment=request_comment,
                **values,
            )
            for values in entries
        ]
        try:
            if len(items) == 1:
                _send_request_email(items[0])
            else:
                _send_request_batch_email(items)
        except Exception as exc:
            logger.exception("Failed to send FPO catalogue batch %s", batch_id)
            transaction.set_rollback(True)
            return Response({"error": f"Unable to send the FPO approval email: {exc}"}, status=503)

    return Response({
        "id": items[0].pk,
        "batch_id": str(batch_id),
        "count": len(items),
        "ids": [item.pk for item in items],
        "entries": [{"id": item.pk, "product": item.product, **{field: getattr(item, field) for field in FIELD_LIMITS}} for item in items],
        "status": "pending",
        "approver": approver_email,
    }, status=201)


@api_view(["POST"])
def acknowledge_fpo_catalogue_request(request, project_id: int, request_id: int):
    project = _get_project(project_id)
    if project is None:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    _email, error = _authorize(request, project)
    if error:
        return error
    if not _request_table_available():
        return Response(
            {"error": "FPO catalogue requests are temporarily unavailable until the database migration is applied."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    try:
        item = FpoCatalogueRequest.objects.get(pk=request_id, project=project)
    except FpoCatalogueRequest.DoesNotExist:
        return Response({"error": "FPO catalogue request not found."}, status=status.HTTP_404_NOT_FOUND)
    if item.status != "approved":
        return Response({"error": "Only approved catalogue requests can be acknowledged."}, status=status.HTTP_409_CONFLICT)

    payload = request.data if isinstance(request.data, dict) else {}
    values = tuple(str(payload.get(key) or "").strip().casefold() for key in ("product", "l1", "l2", "l3", "l4"))
    expected = tuple(str(getattr(item, key)).strip().casefold() for key in ("product", "l1", "l2", "l3", "l4"))
    if values != expected:
        return Response({"error": "The selected Product and L1–L4 must match the approved request."}, status=status.HTTP_400_BAD_REQUEST)

    if item.catalogue_updated_at is None:
        item.catalogue_updated_at = timezone.now()
        item.save(update_fields=["catalogue_updated_at", "updated_at"])
    return Response({"status": "acknowledged", "id": item.pk})


def _prepare_approval_entries(items: list[FpoCatalogueRequest], raw_entries):
    if not isinstance(raw_entries, list) or len(raw_entries) != len(items):
        return None, "Submit each request entry exactly once."

    items_by_id = {item.pk: item for item in items}
    allowed_products = {
        _catalogue_product(str(value or "")).casefold()
        for value in (items[0].project.products or [])
    }
    prepared = {}
    seen = set()
    for index, raw_entry in enumerate(raw_entries, start=1):
        if not isinstance(raw_entry, dict):
            return None, f"Entry {index} must be an object."
        try:
            request_id = int(raw_entry.get("id"))
        except (TypeError, ValueError):
            return None, f"Entry {index} has an invalid request ID."
        if request_id not in items_by_id or request_id in prepared:
            return None, f"Entry {index} does not match a unique request in this batch."

        product = _catalogue_product(str(raw_entry.get("product") or ""))
        if not product or product.casefold() not in allowed_products:
            return None, f"Entry {index}: choose a product from this project's intake."

        values = {"product": product}
        for field, limit in FIELD_LIMITS.items():
            value = str(raw_entry.get(field) or "").strip()
            if not value:
                return None, f"Entry {index}: {field.upper()} is required."
            if len(value) > limit:
                return None, f"Entry {index}: {field.upper()} exceeds {limit} characters."
            values[field] = value

        key = tuple(values[field].casefold() for field in ("product", *FIELD_LIMITS))
        if key in seen:
            return None, f"Entry {index} duplicates another entry in this batch."
        seen.add(key)
        prepared[request_id] = values

    if set(prepared) != set(items_by_id):
        return None, "Submit each request entry exactly once."
    return [prepared[item.pk] for item in items], None


@api_view(["POST"])
def decide_fpo_catalogue_batch(request):
    email = get_request_email(request)
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED)
    if not _request_table_available():
        return Response(
            {"error": "FPO catalogue requests are temporarily unavailable until the database migration is applied."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    payload = request.data if isinstance(request.data, dict) else {}
    try:
        batch_id = UUID(str(payload.get("batch_id") or ""))
    except (TypeError, ValueError):
        return Response({"error": "A valid FPO batch ID is required."}, status=status.HTTP_400_BAD_REQUEST)
    action = str(payload.get("action") or "").strip().lower()
    comment = str(payload.get("comment") or "").strip()
    if action not in {"approved", "rejected"}:
        return Response({"error": "Choose approved or rejected."}, status=status.HTTP_400_BAD_REQUEST)
    if action == "rejected" and not comment:
        return Response({"error": "A comment is required when rejecting a request batch."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        items = list(
            FpoCatalogueRequest.objects.select_for_update()
            .select_related("project")
            .filter(batch_id=batch_id)
            .order_by("id")
        )
        if not items:
            return Response({"error": "FPO request batch not found."}, status=status.HTTP_404_NOT_FOUND)
        if any(item.status != "pending" for item in items):
            return Response({"error": "This FPO request batch has already been decided."}, status=status.HTTP_409_CONFLICT)
        if any(
            item.project_id != items[0].project_id
            or normalize_email(item.requested_by) != normalize_email(items[0].requested_by)
            for item in items
        ):
            return Response({"error": "The FPO request batch contains inconsistent entries."}, status=status.HTTP_409_CONFLICT)
        if not is_super_admin(email) and any(
            normalize_email(item.approver_email) != normalize_email(email)
            for item in items
        ):
            return Response({"error": "You are not authorised to decide this FPO request batch."}, status=status.HTTP_403_FORBIDDEN)

        if action == "approved":
            prepared_entries = None
            if "entries" in payload:
                prepared_entries, error = _prepare_approval_entries(items, payload.get("entries"))
                if error:
                    return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
            if prepared_entries is not None:
                for item, values in zip(items, prepared_entries):
                    item.product = values["product"]
                    for field in FIELD_LIMITS:
                        setattr(item, field, values[field])

            seen = set()
            for item in items:
                key = tuple(str(getattr(item, field)).strip().casefold() for field in ("product", "l1", "l2", "l3", "l4"))
                if key in seen:
                    return Response({"error": "The FPO request batch contains duplicate catalogue entries."}, status=status.HTTP_409_CONFLICT)
                seen.add(key)
                exists = ServiceCatalogue.objects.filter(
                    product__iexact=item.product,
                    l1__iexact=item.l1,
                    l2__iexact=item.l2,
                    l3__iexact=item.l3,
                    l4__iexact=item.l4,
                ).exists()
                if not exists:
                    _insert_service_catalogue_entry(item)

            def clear_catalogue_caches():
                from api.views.opportunity_task_scope import _catalogue, _catalogue_additions

                _catalogue.cache_clear()
                _catalogue_additions.cache_clear()

            transaction.on_commit(clear_catalogue_caches)

        decided_at = timezone.now()
        for item in items:
            item.status = action
            item.decision_comment = comment
            item.decided_by = email
            item.decided_at = decided_at
            item.save(update_fields=["product", *FIELD_LIMITS, "status", "decision_comment", "decided_by", "decided_at", "updated_at"])
        rows = [_serialize_request(item, email, len(items)) for item in items]

    notification_sent = True
    try:
        _send_decision_batch_email(items)
    except Exception:
        notification_sent = False
        logger.exception("FPO batch decision saved but applicant notification failed for batch %s", batch_id)
    return Response({
        "status": "success",
        "batch_id": str(batch_id),
        "rows": rows,
        "notification_sent": notification_sent,
    })


@api_view(["POST"])
def decide_fpo_catalogue_request(request, request_id: int):
    email = get_request_email(request)
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED)
    if not _request_table_available():
        return Response(
            {"error": "FPO catalogue requests are temporarily unavailable until the database migration is applied."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    with transaction.atomic():
        try:
            item = FpoCatalogueRequest.objects.select_for_update().select_related("project").get(pk=request_id)
        except FpoCatalogueRequest.DoesNotExist:
            return Response({"error": "FPO catalogue request not found."}, status=status.HTTP_404_NOT_FOUND)
        if normalize_email(item.approver_email) != normalize_email(email) and not is_super_admin(email):
            return Response({"error": "You are not authorised to decide this FPO request."}, status=status.HTTP_403_FORBIDDEN)
        if item.status != "pending":
            return Response({"error": "This FPO request has already been decided."}, status=status.HTTP_409_CONFLICT)

        payload = request.data if isinstance(request.data, dict) else {}
        action = str(payload.get("action") or "").strip().lower()
        comment = str(payload.get("comment") or "").strip()
        if action not in {"approved", "rejected"}:
            return Response({"error": "Choose approved or rejected."}, status=status.HTTP_400_BAD_REQUEST)
        if action == "rejected" and not comment:
            return Response({"error": "A comment is required when rejecting a request."}, status=status.HTTP_400_BAD_REQUEST)

        if action == "approved":
            if "entry" in payload:
                prepared_entries, error = _prepare_approval_entries([item], [payload.get("entry")])
                if error:
                    return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
                item.product = prepared_entries[0]["product"]
                for field in FIELD_LIMITS:
                    setattr(item, field, prepared_entries[0][field])

            exists = ServiceCatalogue.objects.filter(
                product=item.product,
                l1=item.l1,
                l2=item.l2,
                l3=item.l3,
                l4=item.l4,
            ).exists()
            if not exists:
                _insert_service_catalogue_entry(item)
            from api.views.opportunity_task_scope import _catalogue, _catalogue_additions

            _catalogue.cache_clear()
            _catalogue_additions.cache_clear()

        item.status = action
        item.decision_comment = comment
        item.decided_by = email
        item.decided_at = timezone.now()
        item.save(update_fields=["product", *FIELD_LIMITS, "status", "decision_comment", "decided_by", "decided_at", "updated_at"])
        row = _serialize_request(item, email)

    notification_sent = True
    try:
        _send_decision_email(item)
    except Exception:
        notification_sent = False
        logger.exception("FPO decision saved but applicant notification failed for request %s", item.pk)
    return Response({"status": "success", "row": row, "notification_sent": notification_sent})