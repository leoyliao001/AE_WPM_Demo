import base64
import json
import re
from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from api.models import ProjectAttributesAccess

TABLE_KEYS = (
    "fpo_mapping",
    "product_ownership",
    "gsc_site_mapping",
    "access_control",
)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$|^[^@\s]+@localhost$", re.I)


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _decode_jwt_payload(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload = parts[1]
        padding = "=" * (-len(payload) % 4)
        raw = base64.urlsafe_b64decode(payload + padding)
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def get_request_email(request) -> str:
    """Resolve SSO email from JWT Bearer and/or X-User-Email header."""
    header_email = normalize_email(request.headers.get("X-User-Email", ""))
    auth = request.headers.get("Authorization", "") or ""
    token = ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()

    claims = _decode_jwt_payload(token) if token else {}
    claim_email = normalize_email(
        claims.get("preferred_username")
        or claims.get("upn")
        or claims.get("email")
        or claims.get("unique_name")
        or ""
    )

    # Prefer validated-looking claim; fall back to explicit header (local mock SSO).
    for candidate in (claim_email, header_email):
        if candidate and EMAIL_RE.match(candidate):
            return candidate
    return claim_email or header_email


def build_access_snapshot(email: str) -> dict:
    email = normalize_email(email)
    row = ProjectAttributesAccess.objects.filter(email__iexact=email).first() if email else None
    if not row:
        return {
            "email": email,
            "is_super_admin": False,
            "authenticated": bool(email),
            "tables": {key: False for key in TABLE_KEYS},
        }

    is_super = bool(row.is_super_admin)
    tables = {
        "fpo_mapping": is_super or bool(row.fpo_mapping),
        "product_ownership": is_super or bool(row.product_ownership),
        "gsc_site_mapping": is_super or bool(row.gsc_site_mapping),
        "access_control": is_super or bool(row.access_control),
    }
    return {
        "email": email,
        "is_super_admin": is_super,
        "authenticated": True,
        "tables": tables,
    }


def can_access_table(email: str, table_key: str) -> bool:
    if table_key not in TABLE_KEYS:
        return False
    snapshot = build_access_snapshot(email)
    return bool(snapshot["tables"].get(table_key))


def deny_response(message: str, http_status=status.HTTP_403_FORBIDDEN):
    return Response({"error": message}, status=http_status)


def require_attributes_access(table_key: str):
    """Decorator: require SSO email with access to the given attributes table."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            email = get_request_email(request)
            if not email:
                return deny_response(
                    "Sign in required. Missing SSO email.",
                    status.HTTP_401_UNAUTHORIZED,
                )
            if not can_access_table(email, table_key):
                return deny_response(
                    f"Access denied for {email} on table '{table_key}'."
                )
            request.attributes_email = email
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
