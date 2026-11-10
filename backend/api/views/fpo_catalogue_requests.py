from __future__ import annotations

import logging
import re
from functools import lru_cache

from django.conf import settings
from django.db import DatabaseError, connection, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.html import escape
import requests
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import FpoCatalogueRequest, ServiceCatalogue
from api.permissions.attributes_access import get_request_email, is_super_admin, normalize_email
from api.views.stakeholder_registration import _authorize, _get_project

logger = logging.getLogger(__name__)

FIELD_LIMITS = {"l1": 128, "l2": 128, "l3": 128, "l4": 255}


@lru_cache(maxsize=1)
def _request_table_available() -> bool:
    try:
        return FpoCatalogueRequest._meta.db_table in connection.introspection.table_names()
    except DatabaseError:
        logger.exception("Unable to check FPO catalogue request table availability")
        return False


def _catalogue_product(value: str) -> str:
    return re.sub(r"^General\s+", "", value.strip(), flags=re.IGNORECASE).strip()


def _serialize_request(item: FpoCatalogueRequest, email: str) -> dict:
    approver = normalize_email(item.approver_email) == normalize_email(email)
    requester = normalize_email(item.requested_by) == normalize_email(email)
    decided_by_me = normalize_email(item.decided_by) == normalize_email(email)
    completed = item.status in {"approved", "rejected"}
    return {
        "request_kind": "fpo_catalogue",
        "fpo_request_id": item.pk,
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
    return [_serialize_request(item, email) for item in requests]


def catalogue_request_reminders(project) -> list[dict]:
    if not _request_table_available():
        return []
    return [
        {
            "id": item.pk,
            "product": item.product,
            "l1": item.l1,
            "l2": item.l2,
            "l3": item.l3,
            "l4": item.l4,
            "status": item.status,
            "decision_comment": item.decision_comment,
            "created_at": item.created_at.isoformat(),
        }
        for item in FpoCatalogueRequest.objects.filter(
            project=project, catalogue_updated_at__isnull=True
        ).order_by("-created_at", "id")
    ]


def _send_request_email(item: FpoCatalogueRequest) -> None:
    base_url = getattr(settings, "DJANGO_PUBLIC_BASE_URL", "").rstrip("/")
    review_url = f"{base_url}/approval-cycle?fpo_request={item.pk}"
    subject = f"FPO approval requested: Service Catalogue entry for {item.project.migration_request_id}"
    text_body = "\n".join([
        "A new Service Catalogue entry requires FPO review.",
        "",
        "This request was created because the requester selected 'Not in Service Catalog' in Opportunity Assessment.",
        f"Project: {item.project.project_name}",
        f"Migration Request ID: {item.project.migration_request_id}",
        f"Product: {item.product}",
        f"L1: {item.l1}",
        f"L2: {item.l2}",
        f"L3: {item.l3}",
        f"L4: {item.l4}",
        f"Requested by: {item.requested_by}",
        "",
        f"Review this request in Approval Cycle: {review_url}",
        "The entry will be added to Service Catalogue only after approval.",
    ])
    html_body = f"""
        <p>A new Service Catalogue entry requires FPO review.</p>
        <p>This request was created because the requester selected <strong>Not in Service Catalog</strong> in Opportunity Assessment.</p>
        <table>
            <tr><th align="left">Project</th><td>{escape(item.project.project_name)}</td></tr>
            <tr><th align="left">Migration Request ID</th><td>{escape(item.project.migration_request_id)}</td></tr>
            <tr><th align="left">Product</th><td>{escape(item.product)}</td></tr>
            <tr><th align="left">L1</th><td>{escape(item.l1)}</td></tr>
            <tr><th align="left">L2</th><td>{escape(item.l2)}</td></tr>
            <tr><th align="left">L3</th><td>{escape(item.l3)}</td></tr>
            <tr><th align="left">L4</th><td>{escape(item.l4)}</td></tr>
            <tr><th align="left">Requested by</th><td>{escape(item.requested_by)}</td></tr>
        </table>
        <p><a href="{escape(review_url)}">Open Approval Cycle to review this request</a></p>
        <p>The entry will be added to Service Catalogue only after approval.</p>
    """
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
            "personalizations": [{"to": [{"email": item.approver_email}]}],
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

    values = {}
    for field, limit in FIELD_LIMITS.items():
        value = str(payload.get(field) or "").strip()
        if not value:
            return Response({"error": f"{field.upper()} is required."}, status=status.HTTP_400_BAD_REQUEST)
        if len(value) > limit:
            return Response({"error": f"{field.upper()} exceeds {limit} characters."}, status=status.HTTP_400_BAD_REQUEST)
        values[field] = value

    exists = ServiceCatalogue.objects.filter(
        product__iexact=product,
        l1__iexact=values["l1"],
        l2__iexact=values["l2"],
        l3__iexact=values["l3"],
        l4__iexact=values["l4"],
    ).exists()
    if exists:
        return Response({"error": "This Product and L1–L4 combination is already in Service Catalogue."}, status=status.HTTP_409_CONFLICT)

    approver_email = getattr(settings, "FPO_CATALOGUE_APPROVER_EMAIL", "leo.y.liao@lns.maersk.com")
    with transaction.atomic():
        item = FpoCatalogueRequest.objects.create(
            project=project,
            product=product,
            requested_by=email,
            approver_email=approver_email,
            **values,
        )
        try:
            _send_request_email(item)
        except Exception as exc:
            logger.exception("Failed to send FPO catalogue request %s", item.pk)
            transaction.set_rollback(True)
            return Response({"error": f"Unable to send the FPO approval email: {exc}"}, status=503)

    return Response({"id": item.pk, "status": item.status, "approver": item.approver_email}, status=201)


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


@api_view(["POST"])
@transaction.atomic
def decide_fpo_catalogue_request(request, request_id: int):
    email = get_request_email(request)
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED)
    if not _request_table_available():
        return Response(
            {"error": "FPO catalogue requests are temporarily unavailable until the database migration is applied."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
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
    item.save(update_fields=["status", "decision_comment", "decided_by", "decided_at", "updated_at"])
    return Response({"status": "success", "row": _serialize_request(item, email)})