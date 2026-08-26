"""
Approval Cycle — the live approval queue + decision endpoint that back the
Approval Cycle page (frontend/src/views/ApprovalCycle.vue).

Requests come straight from migration_intake_submission; approval progress is
persisted on approval_workflow (keyed by migration_request_id); who is allowed
to decide each stage is resolved from approval_input (function + product ->
approver email per role).
"""

from __future__ import annotations

import logging
import threading

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import ApprovalWorkflow, MigrationIntakeSubmission
from api.permissions.approval_access import (
    get_request_email,
    load_approval_input_rows,
    recipients_for_role,
    roles_for,
)
from api.services.approval_notifications import (
    send_next_stage_notification,
    send_return_notification,
)

logger = logging.getLogger(__name__)

SEQUENTIAL_ROLES = ["area_head", "pmo", "bpm"]
PARALLEL_ROLES = ["elt", "gsc_head"]
ALL_ROLES = SEQUENTIAL_ROLES + ["fbp", "wpm"] + PARALLEL_ROLES
VALID_ACTIONS = {"approved", "rejected", "returned", "delegated", "reassigned"}

ROLE_FIELD_MAP = {
    "area_head": {"status": "area_head_status", "comment": "area_head_comments", "date": "area_head_final_date", "approver": "area_head_approved_by"},
    "pmo": {"status": "pmo_status", "comment": "pmo_review_comment", "date": "pmo_review_date", "approver": "pmo_approved_by"},
    "bpm": {"status": "bpm_status", "comment": "bpm_comment", "date": "bpm_review_date", "approver": "bpm_approved_by"},
    "fbp": {"status": "fbp_status", "comment": "fbp_comment", "date": "fbp_review_date", "approver": "fbp_approved_by"},
    "wpm": {"status": "wpm_review_status", "comment": "wpm_review_comment", "date": "wpm_review_date", "approver": "wpm_approved_by"},
    "elt": {"status": "elt_status", "comment": "elt_comment", "date": "elt_date", "approver": "elt_approved_by"},
    "gsc_head": {"status": "gsc_head_status", "comment": "gsc_head_comment", "date": "gsc_head_date", "approver": "gsc_head_approved_by"},
}


class _EmptyWorkflow:
    """Stand-in for requests that have no approval_workflow row yet."""

    def __getattr__(self, _name):
        return ""


def _progress(workflow) -> dict:
    budget_status = (getattr(workflow, "bpm_budget_status", "") or "").strip().lower()
    if budget_status not in {"within", "beyond"}:
        budget_status = "pending"
    beyond_budget = budget_status == "beyond"
    seq_roles = SEQUENTIAL_ROLES + (["fbp"] if beyond_budget else []) + ["wpm"]
    seq_len = len(seq_roles)

    step = seq_len + 1
    for i, role in enumerate(seq_roles, start=1):
        if (getattr(workflow, ROLE_FIELD_MAP[role]["status"], "") or "") != "approved":
            step = i
            break

    parallel = {
        role: (getattr(workflow, ROLE_FIELD_MAP[role]["status"], "") or "pending") for role in PARALLEL_ROLES
    }

    return {
        "step": step,
        "seqLen": seq_len,
        "budgetStatus": budget_status,
        "beyondBudget": beyond_budget,
        "seqRoles": seq_roles,
        "parallel": parallel,
        "completed": parallel["elt"] == "approved" and parallel["gsc_head"] == "approved",
    }


def _current_role(progress: dict):
    if progress["step"] <= progress["seqLen"]:
        return progress["seqRoles"][progress["step"] - 1]
    return None  # parallel phase — elt & gsc_head are both current


def _is_actionable(progress: dict, my_roles: set) -> bool:
    role = _current_role(progress)
    if role:
        return role in my_roles
    return any(
        role in my_roles and progress["parallel"][role] in {"pending", "returned"}
        for role in PARALLEL_ROLES
    )


def _previous_role(progress: dict, role: str) -> str | None:
    if role in PARALLEL_ROLES:
        return "wpm"
    seq_roles = progress["seqRoles"]
    try:
        index = seq_roles.index(role)
    except ValueError:
        return None
    return seq_roles[index - 1] if index > 0 else None


def _notify_return_owner(submission, role: str, comment: str, approval_rows) -> None:
    def send():
        try:
            send_return_notification(submission, role, comment, approval_rows)
        except Exception:
            logger.exception("Failed to notify returned %s approver(s) for %s", role, submission.migration_request_id)

    threading.Thread(target=send, daemon=True).start()


def _notify_next_approvers(submission, progress: dict, approval_rows, completed_role: str) -> None:
    next_role = _current_role(progress)
    if next_role:
        next_roles = [next_role]
    elif completed_role == "wpm":
        next_roles = [role for role in PARALLEL_ROLES if progress["parallel"][role] == "pending"]
    else:
        next_roles = []

    for role in next_roles:
        def send(role_to_notify=role):
            try:
                send_next_stage_notification(submission, role_to_notify, approval_rows)
            except Exception:
                logger.exception(
                    "Failed to notify %s approver(s) for %s",
                    role_to_notify,
                    submission.migration_request_id,
                )

        threading.Thread(target=send, daemon=True).start()


def _join_list(values) -> list:
    return [str(v).strip() for v in values if str(v or "").strip()] if isinstance(values, list) else []


def _serialize_row(submission: MigrationIntakeSubmission, workflow, progress: dict, my_roles: set, approval_rows) -> dict:
    return {
        "migration_request_id": submission.migration_request_id,
        "project_name": submission.project_name,
        "migration_type": submission.migration_type,
        "migration_type_value": submission.migration_type_value,
        "requestor": submission.requestor,
        "region": submission.region,
        "areas": _join_list(submission.areas),
        "countries": _join_list(submission.countries),
        "function_name": submission.function_name,
        "products": _join_list(submission.products),
        "proposed_scope": submission.proposed_scope,
        "fte_number": submission.fte_number,
        "jl2": submission.jl2,
        "jl3": submission.jl3,
        "jl4": submission.jl4,
        "job_level_total": submission.job_level_total,
        "requested_date": submission.requested_date,
        "businessCaseSubmittedAt": (
            getattr(workflow, "business_case_submitted_date", None)
            or submission.business_case_submission_date
        ),
        "status": submission.status,
        "step": progress["step"],
        "totalSteps": progress["seqLen"] + len(PARALLEL_ROLES),
        "budgetStatus": progress["budgetStatus"],
        "beyondBudget": progress["beyondBudget"],
        "currentRole": _current_role(progress),
        "parallel": {"elt": progress["parallel"]["elt"] or "pending", "gscHead": progress["parallel"]["gsc_head"] or "pending"},
        "completed": progress["completed"],
        "myRoles": sorted(my_roles),
        "actionable": _is_actionable(progress, my_roles),
        "responsibleApprovers": {
            role: recipients_for_role(role, submission.function_name, submission.products, approval_rows)
            for role in ALL_ROLES
        },
        "decisions": {
            role: {
                "status": getattr(workflow, ROLE_FIELD_MAP[role]["status"], "") or "",
                "comment": getattr(workflow, ROLE_FIELD_MAP[role]["comment"], "") or "",
                "date": getattr(workflow, ROLE_FIELD_MAP[role]["date"], None),
                "approvedBy": getattr(workflow, ROLE_FIELD_MAP[role]["approver"], "") or "",
            }
            for role in ALL_ROLES
        },
    }


@api_view(["GET"])
def list_approval_queue(request):
    """Requests from migration intake, merged with live approval progress."""
    email = get_request_email(request)
    if not email:
        return Response(
            {"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED
        )

    approval_rows = load_approval_input_rows()
    workflows = {w.migration_request_id: w for w in ApprovalWorkflow.objects.all()}

    rows = []
    for submission in MigrationIntakeSubmission.objects.all().order_by("-created_at", "id"):
        workflow = workflows.get(submission.migration_request_id) or _EmptyWorkflow()
        progress = _progress(workflow)
        my_roles = roles_for(email, submission.function_name, submission.products, approval_rows)
        rows.append(_serialize_row(submission, workflow, progress, my_roles, approval_rows))

    return Response({"email": email, "count": len(rows), "rows": rows})


@api_view(["POST"])
def submit_approval_decision(request):
    """Record a decision for one role/stage of one request, after checking access."""
    email = get_request_email(request)
    if not email:
        return Response(
            {"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED
        )

    migration_request_id = str(request.data.get("migration_request_id") or "").strip()
    role = str(request.data.get("role") or "").strip()
    action = str(request.data.get("action") or "").strip()
    comment = str(request.data.get("comment") or "").strip()
    budget_status = str(request.data.get("budget_status") or "").strip()

    if not migration_request_id or role not in ROLE_FIELD_MAP or action not in VALID_ACTIONS:
        return Response({"error": "migration_request_id, a valid role and action are required."}, status=status.HTTP_400_BAD_REQUEST)
    if action != "approved" and not comment:
        return Response({"error": "A comment is required for this action."}, status=status.HTTP_400_BAD_REQUEST)
    if role == "bpm" and action == "approved" and budget_status not in {"within", "beyond"}:
        return Response({"error": "budget_status must be 'within' or 'beyond'."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        submission = MigrationIntakeSubmission.objects.get(migration_request_id=migration_request_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return Response({"error": "Request not found."}, status=status.HTTP_404_NOT_FOUND)

    workflow, _created = ApprovalWorkflow.objects.get_or_create(migration_request_id=migration_request_id)

    approval_rows = load_approval_input_rows()
    my_roles = roles_for(email, submission.function_name, submission.products, approval_rows)
    progress = _progress(workflow)
    current_role = _current_role(progress)

    if current_role:
        if role != current_role:
            return Response({"error": f"'{role}' is not the current stage for this request."}, status=status.HTTP_409_CONFLICT)
    elif role not in PARALLEL_ROLES or progress["parallel"][role] not in {"pending", "returned"}:
        return Response({"error": f"'{role}' has already decided or is not active for this request."}, status=status.HTTP_409_CONFLICT)

    if role not in my_roles:
        return Response(
            {"error": f"{email} is not an authorised '{role}' approver for this function/product."},
            status=status.HTTP_403_FORBIDDEN,
        )

    previous_role = _previous_role(progress, role) if action == "returned" else None
    if action == "returned" and not previous_role:
        return Response(
            {"error": "Area Head is the first approval stage and cannot return the request to an earlier owner."},
            status=status.HTTP_409_CONFLICT,
        )

    fields = ROLE_FIELD_MAP[role]
    setattr(workflow, fields["status"], action)
    setattr(workflow, fields["comment"], comment)
    setattr(workflow, fields["date"], timezone.now())
    setattr(workflow, fields["approver"], email)
    if role == "bpm" and action == "approved":
        workflow.bpm_budget_status = budget_status
    if action == "returned":
        previous_fields = ROLE_FIELD_MAP[previous_role]
        setattr(workflow, previous_fields["status"], "")
        setattr(workflow, previous_fields["date"], None)
        setattr(workflow, previous_fields["approver"], "")
    workflow.save()

    updated_progress = _progress(workflow)
    if action == "approved":
        _notify_next_approvers(submission, updated_progress, approval_rows, role)
    elif action == "returned":
        _notify_return_owner(submission, previous_role, comment, approval_rows)
    return Response(
        {
            "status": "success",
            "migration_request_id": migration_request_id,
            "row": _serialize_row(submission, workflow, updated_progress, my_roles, approval_rows),
        }
    )
