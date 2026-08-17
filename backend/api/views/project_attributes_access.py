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
    ("access_control", "Access Control (Y/N)"),
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
    "access_control",
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
            "access_control": "Y",
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
        "access_control": _yn(item.access_control),
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
                    "access_control": False,
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
