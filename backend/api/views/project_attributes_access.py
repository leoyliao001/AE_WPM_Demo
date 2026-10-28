"""
Project Attributes Access Control — SSO email permissions for attribute tables.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import ProjectAttributesAccess
from api.permissions.attributes_access import (
    build_access_snapshot,
    get_request_email,
    normalize_email,
    require_attributes_access,
)

ALL_FIELDS = [
    ("email", "Email"),
    ("is_super_admin", "Super Admin (Y/N)"),
    ("fpo_mapping", "FPO Mapping (Y/N)"),
    ("product_ownership", "Product Ownership (Y/N)"),
    ("gsc_site_mapping", "GSC Site Mapping (Y/N)"),
    ("service_catalogue", "Service Catalogue (Y/N)"),
    ("working_hours", "Working Hours (Y/N)"),
    ("project_gantt", "Project Gantt (Y/N)"),
    ("migration_intake", "Migration Intake (Y/N)"),
    ("approval_workflow", "Approval Workflow (Y/N)"),
    ("input_for_approval", "Input for Approval (Y/N)"),
    ("bpm_rofo", "BPM ROFO (Y/N)"),
    ("bpm_actual", "BPM Actual (Y/N)"),
    ("access_control", "Access Control (Y/N)"),
    ("scope_statement", "Scope Statement (Y/N)"),
    ("stakeholder_registration", "Stakeholder Registration (Y/N)"),
    ("project_charter", "Project Charter (Y/N)"),
    ("business_case", "Business Case (Y/N)"),
    ("cost_rates", "Business Case Cost Rates (Y/N)"),
    ("resources", "Resources (Y/N)"),
    ("access_enablement", "Access & Enablement (Y/N)"),
    ("business_impact_analysis", "Business Impact Analysis (Y/N)"),
]

BOOL_FIELDS = {
    "is_super_admin",
    "fpo_mapping",
    "product_ownership",
    "gsc_site_mapping",
    "service_catalogue",
    "working_hours",
    "project_gantt",
    "migration_intake",
    "approval_workflow",
    "input_for_approval",
    "bpm_rofo",
    "bpm_actual",
    "access_control",
    "scope_statement",
    "stakeholder_registration",
    "project_charter",
    "business_case",
    "cost_rates",
    "resources",
    "access_enablement",
    "business_impact_analysis",
}


def _yn(value: bool) -> str:
    return "Y" if value else "N"


def _serialize_row(item: ProjectAttributesAccess) -> dict:
    # Super Admin effectively has every table; surface that so the grid matches runtime ACL.
    if item.is_super_admin:
        return {
            "id": item.id,
            "email": item.email,
            "is_super_admin": "Y",
            "fpo_mapping": "Y",
            "product_ownership": "Y",
            "gsc_site_mapping": "Y",
            "service_catalogue": "Y",
            "working_hours": "Y",
            "project_gantt": "Y",
            "migration_intake": "Y",
            "approval_workflow": "Y",
            "input_for_approval": "Y",
            "bpm_rofo": "Y",
            "bpm_actual": "Y",
            "access_control": "Y",
            "scope_statement": "Y",
            "stakeholder_registration": "Y",
            "project_charter": "Y",
            "business_case": "Y",
            "cost_rates": "Y",
            "resources": "Y",
            "access_enablement": "Y",
            "business_impact_analysis": "Y",
        }
    return {
        "id": item.id,
        "email": item.email,
        "is_super_admin": _yn(item.is_super_admin),
        "fpo_mapping": _yn(item.fpo_mapping),
        "product_ownership": _yn(item.product_ownership),
        "gsc_site_mapping": _yn(item.gsc_site_mapping),
        "service_catalogue": _yn(item.service_catalogue),
        "working_hours": _yn(item.working_hours),
        "project_gantt": _yn(item.project_gantt),
        "migration_intake": _yn(item.migration_intake),
        "approval_workflow": _yn(item.approval_workflow),
        "input_for_approval": _yn(item.input_for_approval),
        "bpm_rofo": _yn(item.bpm_rofo),
        "bpm_actual": _yn(item.bpm_actual),
        "access_control": _yn(item.access_control),
        "scope_statement": _yn(item.scope_statement),
        "stakeholder_registration": _yn(item.stakeholder_registration),
        "project_charter": _yn(item.project_charter),
        "business_case": _yn(item.business_case),
        "cost_rates": _yn(item.cost_rates),
        "resources": _yn(item.resources),
        "access_enablement": _yn(item.access_enablement),
        "business_impact_analysis": _yn(item.business_impact_analysis),
    }


@api_view(["GET"])
def my_attributes_access(request):
    """Return current SSO user's access snapshot (no table ACL required)."""
    email = get_request_email(request)
    if not email:
        return Response(
            {
                "email": "",
                "is_super_admin": False,
                "authenticated": False,
                "tables": {
                    "fpo_mapping": False,
                    "product_ownership": False,
                    "gsc_site_mapping": False,
                    "service_catalogue": False,
                    "working_hours": False,
                    "project_gantt": False,
                    "migration_intake": False,
                    "approval_workflow": False,
                    "input_for_approval": False,
                    "bpm_rofo": False,
                    "bpm_actual": False,
                    "access_control": False,
                    "scope_statement": False,
                    "stakeholder_registration": False,
                    "project_charter": False,
                    "business_case": False,
                    "cost_rates": False,
                    "resources": False,
                    "access_enablement": False,
                    "business_impact_analysis": False,
                },
            }
        )
    return Response(build_access_snapshot(email))


@api_view(["GET"])
@require_attributes_access("access_control")
def list_project_attributes_access(_request):
    rows = [
        _serialize_row(item)
        for item in ProjectAttributesAccess.objects.all().order_by("email")
    ]
    return Response(
        {
            "count": len(rows),
            "columns": [{"key": key, "label": label} for key, label in ALL_FIELDS],
            "rows": rows,
        }
    )
