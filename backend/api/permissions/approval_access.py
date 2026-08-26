"""
Approval Cycle role resolution — who can act as Area Head / PMO / BPM / FBP /
ELT / GSC Head for a given function + product, per the approval_input table.
"""

import re

from api.models import ApprovalInput
from api.permissions.attributes_access import get_request_email, normalize_email

ROLE_FIELDS = ("area_head", "pmo", "bpm", "fbp", "wpm", "elt", "gsc_head")

EMAIL_SPLIT_RE = re.compile(r"[;,]")


def _split_emails(value: str) -> set:
    if not value:
        return set()
    return {normalize_email(part) for part in EMAIL_SPLIT_RE.split(value) if part.strip()}


def load_approval_input_rows():
    """Fetch the whole approval_input table once (small reference table)."""
    return list(ApprovalInput.objects.all())


def roles_for(email: str, function_name: str, products, rows=None) -> set:
    """Roles `email` holds for `function_name` + any of `products` (case-insensitive)."""
    email = normalize_email(email)
    if not email:
        return set()

    function_key = (function_name or "").strip().lower()
    product_keys = {str(p).strip().lower() for p in (products or []) if str(p).strip()}
    if rows is None:
        rows = load_approval_input_rows()

    roles = set()
    for row in rows:
        if (row.activity_function or "").strip().lower() != function_key:
            continue
        if product_keys and (row.product or "").strip().lower() not in product_keys:
            continue
        for field in ROLE_FIELDS:
            if email in _split_emails(getattr(row, field, "")):
                roles.add(field)
    return roles


__all__ = ["ROLE_FIELDS", "get_request_email", "load_approval_input_rows", "roles_for"]
