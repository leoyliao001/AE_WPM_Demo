import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4

from django.db import transaction
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from api.models import (
    MigrationIntakeSubmission,
    ScopeStatement,
    ScopeStatementEvidence,
    ScopeStatementLine,
)
from api.permissions.attributes_access import (
    can_access_table,
    get_request_email,
    normalize_email,
    require_attributes_access,
)

JOB_LEVELS = ("JL2", "JL3", "JL4")
MAX_EVIDENCE_BYTES = 20 * 1024 * 1024
EVIDENCE_EXTENSIONS = {".pdf", ".docx", ".msg", ".xlsx"}
MAX_FTE = Decimal("99999999.9999")


def _resolve_user_email(request):
    email = normalize_email(get_request_email(request))
    if not email:
        return None
    return email


def _has_scope_statement_access(project, email):
    return (
        normalize_email(email) == normalize_email(project.requestor)
        or can_access_table(email, "scope_statement")
    )


def _scope_statement_access_denied():
    return Response(
        {"error": "Access denied. Only the project requestor or users with Access Control access can view this Scope Statement."},
        status=status.HTTP_403_FORBIDDEN,
    )


def _get_project(project_id):
    try:
        return MigrationIntakeSubmission.objects.get(pk=project_id)
    except MigrationIntakeSubmission.DoesNotExist:
        return None


def _statement_for_project(project, *, for_update=False):
    statements = ScopeStatement.objects.filter(project=project)
    if for_update:
        statements = statements.select_for_update()
    return statements.prefetch_related("lines__evidence", "attachments").first()


def _number(value, label, *, allow_none=False, whole=False):
    if value in (None, ""):
        if allow_none:
            return None
        raise ValueError(f"{label} is required.")
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number.")
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"{label} must be a number.")
    if not number.is_finite() or number < 0 or number > MAX_FTE:
        raise ValueError(f"{label} must be between 0 and {MAX_FTE}.")
    if whole and number != number.to_integral_value():
        raise ValueError(f"{label} must be a whole number.")
    return int(number) if whole else number


def _serialize_statement(project, statement, email):
    lines = {line.job_level: line for line in (statement.lines.all() if statement else [])}
    items = []
    for job_level in JOB_LEVELS:
        line = lines.get(job_level)
        items.append({
            "jobLevel": job_level,
            "agreedFte": str(line.agreed_fte) if line and line.agreed_fte is not None else None,
            "notAgreedFte": str(line.not_agreed_fte) if line and line.not_agreed_fte is not None else None,
            "finalFte": line.final_fte if line else None,
            "lockedAt": line.locked_at.isoformat() if line and line.locked_at else None,
            "lockedBy": line.locked_by if line else "",
            "evidence": [
                {
                    "id": item.id,
                    "name": item.file_name,
                    "size": item.file_size,
                    "uploadedBy": item.uploaded_by,
                    "uploadedAt": item.uploaded_at.isoformat(),
                }
                for item in (line.evidence.all() if line else [])
            ],
        })

    return {
        "projectId": project.id,
        "migrationRequestId": project.migration_request_id,
        "projectName": project.project_name,
        "requestor": project.requestor,
        "status": statement.status if statement else "draft",
        "reviewRequired": statement.review_required if statement else False,
        "saved": bool(statement),
        "canEdit": bool(email and _has_scope_statement_access(project, email)) and not (statement and statement.status == "submitted"),
        "revision": statement.revision if statement else 0,
        "scopeText": statement.scope_text if statement else "",
        "outOfScope": statement.out_of_scope if statement else "",
        "assumptions": statement.assumptions if statement else "",
        "waves": statement.waves if statement else [],
        "ambitionFte": str(statement.ambition_fte) if statement and statement.ambition_fte is not None else str(project.fte_number or "0"),
        "finalProjectFte": statement.final_project_fte if statement else None,
        "migratableFte": str(statement.migratable_fte) if statement and statement.migratable_fte is not None else None,
        "migratableFteConfirmed": statement.migratable_fte_confirmed if statement else False,
        "submittedAt": statement.submitted_at.isoformat() if statement and statement.submitted_at else None,
        "submittedBy": statement.submitted_by if statement else "",
        "auditLog": statement.audit_log if statement else [],
        "lines": items,
        "pageLocked": any(line.locked_at for line in lines.values()),
        "attachments": [
            {"id": item.id, "name": item.file_name, "size": item.file_size,
             "uploadedBy": item.uploaded_by, "uploadedAt": item.uploaded_at.isoformat()}
            for item in (statement.attachments.all() if statement else [])
        ],
    }


SCOPE_STATEMENT_DATABASE_COLUMNS = [
    {"key": "migration_request_id", "label": "Migration Request ID", "editable": "new"},
    {"key": "project_name", "label": "Project Name"},
    {"key": "requestor", "label": "Requestor"},
    {"key": "intake_fte", "label": "Intake FTE"},
    {"key": "scope_text", "label": "Scope Statement", "editable": True},
    {"key": "out_of_scope", "label": "Out of Scope", "editable": True},
    {"key": "assumptions", "label": "Assumptions", "editable": True},
    {"key": "waves", "label": "Migration Waves (JSON)", "editable": True},
    {"key": "scope_status", "label": "Scope Status"},
    {"key": "revision", "label": "Revision"},
    {"key": "ambition_fte", "label": "Ambition FTE"},
    {"key": "final_project_fte", "label": "Final Project FTE"},
    {"key": "migratable_fte", "label": "Migratable FTE (manual)"},
    {"key": "migratable_fte_confirmed", "label": "Migratable FTE Confirmed"},
    {"key": "submitted_at", "label": "Submitted At"},
    {"key": "submitted_by", "label": "Submitted By"},
    {"key": "updated_at", "label": "Last Updated"},
    {"key": "audit_log", "label": "Audit Log"},
    {"key": "attachments", "label": "Attachement"},
    *[
            {
                "key": f"{level.lower()}_{field}",
                "label": f"{level} {label}",
                "editable": field in {"agreed_fte", "not_agreed_fte", "final_fte"},
            }
        for level in JOB_LEVELS
        for field, label in (
            ("agreed_fte", "Agreed FTE"),
            ("not_agreed_fte", "Not Agreed FTE"),
            ("final_fte", "Final FTE"),
            ("locked_at", "Locked At"),
            ("locked_by", "Locked By"),
        )
    ],
]


@api_view(["GET"])
@require_attributes_access("scope_statement")
def list_scope_statement_database(_request):
    statements = (
        ScopeStatement.objects.select_related("project")
        .prefetch_related("lines__evidence", "attachments")
        .order_by("project__migration_request_id")
    )
    rows = []
    for statement in statements:
        project = statement.project
        lines = {line.job_level: line for line in statement.lines.all()}
        row = {
            "statement_id": statement.id,
            "project_id": project.id,
            "migration_request_id": project.migration_request_id,
            "project_name": project.project_name,
            "requestor": project.requestor,
            "intake_fte": project.fte_number,
            "scope_text": statement.scope_text,
            "out_of_scope": statement.out_of_scope,
            "assumptions": statement.assumptions,
            "waves": json.dumps(statement.waves),
            "scope_status": statement.status,
            "revision": statement.revision,
            "ambition_fte": str(statement.ambition_fte) if statement.ambition_fte is not None else str(project.fte_number or "0"),
            "final_project_fte": statement.final_project_fte,
            "migratable_fte": str(statement.migratable_fte) if statement.migratable_fte is not None else "",
            "migratable_fte_confirmed": statement.migratable_fte_confirmed,
            "submitted_at": statement.submitted_at.isoformat() if statement.submitted_at else "",
            "submitted_by": statement.submitted_by,
            "updated_at": statement.updated_at.isoformat(),
            "audit_log": json.dumps(statement.audit_log or [], ensure_ascii=False),
            "attachments": json.dumps([
                {"name": item.file_name, "size": item.file_size,
                 "uploadedBy": item.uploaded_by, "uploadedAt": item.uploaded_at.isoformat()}
                for item in statement.attachments.all()
            ], ensure_ascii=False),
        }
        for job_level in JOB_LEVELS:
            prefix = job_level.lower()
            line = lines.get(job_level)
            evidence = list(line.evidence.all()) if line else []
            row.update({
                f"{prefix}_agreed_fte": str(line.agreed_fte) if line and line.agreed_fte is not None else "",
                f"{prefix}_not_agreed_fte": str(line.not_agreed_fte) if line and line.not_agreed_fte is not None else "",
                f"{prefix}_final_fte": line.final_fte if line and line.final_fte is not None else "",
                f"{prefix}_locked_at": line.locked_at.isoformat() if line and line.locked_at else "",
                f"{prefix}_locked_by": line.locked_by if line else "",
                f"{prefix}_evidence": json.dumps([
                    {
                        "name": item.file_name,
                        "size": item.file_size,
                        "uploadedBy": item.uploaded_by,
                        "uploadedAt": item.uploaded_at.isoformat(),
                    }
                    for item in evidence
                ], ensure_ascii=False),
            })
        rows.append(row)

    return Response({"count": len(rows), "columns": SCOPE_STATEMENT_DATABASE_COLUMNS, "rows": rows})


@api_view(["POST"])
@require_attributes_access("scope_statement")
def save_scope_statement_database(request):
    unique_data = request.data.get("uniqueData")
    if not isinstance(unique_data, list) or not unique_data:
        return Response({"error": "uniqueData must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

    created_ids = []
    updated_ids = []
    errors = []
    email = request.attributes_email

    for index, item in enumerate(unique_data):
        if not isinstance(item, dict):
            errors.append({"index": index, "error": "Row must be an object."})
            continue
        record_id = item.get("statement_id")
        try:
            with transaction.atomic():
                if record_id not in (None, ""):
                    statement = ScopeStatement.objects.select_for_update().get(pk=int(record_id))
                    project = statement.project
                    is_new = False
                else:
                    migration_request_id = str(item.get("migration_request_id") or "").strip()
                    if not migration_request_id:
                        raise ValueError("Migration Request ID is required for a new row.")
                    project = MigrationIntakeSubmission.objects.select_for_update().filter(
                        migration_request_id__iexact=migration_request_id
                    ).first()
                    if project is None:
                        raise ValueError(f"Migration Request ID '{migration_request_id}' was not found.")
                    statement, is_new = ScopeStatement.objects.get_or_create(
                        project=project,
                        defaults={"ambition_fte": _number(project.fte_number, "Intake FTE", allow_none=True)},
                    )

                if statement.status == "submitted":
                    raise ValueError("Submitted Scope Statements are frozen.")
                if statement.lines.filter(locked_at__isnull=False).exists():
                    raise ValueError("Scope Statement is locked. Unlock the page before editing.")

                scope_text = item.get("scope_text", statement.scope_text)
                if not isinstance(scope_text, str):
                    raise ValueError("Scope Statement must be text.")
                statement.scope_text = scope_text[:2000]
                _apply_scope_extensions(statement, {
                    "outOfScope": item.get("out_of_scope", statement.out_of_scope),
                    "assumptions": item.get("assumptions", statement.assumptions),
                    "waves": item.get("waves", statement.waves),
                })

                for job_level in JOB_LEVELS:
                    prefix = job_level.lower()
                    line, _ = ScopeStatementLine.objects.get_or_create(
                        statement=statement,
                        job_level=job_level,
                    )
                    values = {
                        "agreed_fte": _number(
                            item.get(f"{prefix}_agreed_fte", line.agreed_fte),
                            f"{job_level} agreed FTE",
                            allow_none=True,
                        ),
                        "not_agreed_fte": _number(
                            item.get(f"{prefix}_not_agreed_fte", line.not_agreed_fte),
                            f"{job_level} exception FTE",
                            allow_none=True,
                        ),
                        "final_fte": _number(
                            item.get(f"{prefix}_final_fte", line.final_fte),
                            f"{job_level} final FTE",
                            allow_none=True,
                            whole=True,
                        ),
                    }
                    if line.locked_at and any(
                        getattr(line, field) != value for field, value in values.items()
                    ):
                        raise ValueError(f"{job_level} is locked. Unlock it on the Scope Statement page before editing.")
                    for field, value in values.items():
                        setattr(line, field, value)
                    line.save(update_fields=list(values))

                if statement.ambition_fte is None:
                    statement.ambition_fte = _number(project.fte_number, "Intake FTE", allow_none=True)
                statement.revision += 1
                statement.audit_log.append({
                    "action": "admin_save",
                    "by": email,
                    "at": timezone.now().isoformat(),
                })
                statement.save()
                (created_ids if is_new else updated_ids).append(statement.id)
        except ScopeStatement.DoesNotExist:
            errors.append({"id": record_id, "error": "Scope Statement not found."})
        except (TypeError, ValueError, InvalidOperation) as exc:
            errors.append({"id": record_id, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            errors.append({"id": record_id, "error": str(exc)})

    success_count = len(created_ids) + len(updated_ids)
    result_status = "success" if not errors else ("partial_success" if success_count else "error")
    http_status = status.HTTP_200_OK if success_count else status.HTTP_400_BAD_REQUEST
    return Response({
        "status": result_status,
        "created_count": len(created_ids),
        "updated_count": len(updated_ids),
        "created_ids": created_ids,
        "updated_ids": updated_ids,
        "error_count": len(errors),
        "errors": errors,
    }, status=http_status)


@api_view(["DELETE"])
@require_attributes_access("scope_statement")
def delete_scope_statement_database(request):
    removed_ids = request.data.get("removedIds")
    if not isinstance(removed_ids, list) or not removed_ids:
        return Response({"error": "removedIds must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

    deleted_ids = []
    errors = []
    for record_id in removed_ids:
        try:
            statement = ScopeStatement.objects.get(pk=int(record_id))
            evidence = list(statement.attachments.all())
            statement.delete()
            for item in evidence:
                if item.file and item.file.name:
                    storage = item.file.storage
                    file_name = item.file.name
                    transaction.on_commit(lambda storage=storage, file_name=file_name: storage.delete(file_name))
            deleted_ids.append(int(record_id))
        except (TypeError, ValueError) as exc:
            errors.append({"id": record_id, "error": f"Invalid id: {exc}"})
        except ScopeStatement.DoesNotExist:
            errors.append({"id": record_id, "error": "Scope Statement not found."})
        except Exception as exc:  # noqa: BLE001
            errors.append({"id": record_id, "error": str(exc)})

    success_count = len(deleted_ids)
    result_status = "success" if not errors else ("partial_success" if success_count else "error")
    http_status = status.HTTP_200_OK if success_count else status.HTTP_400_BAD_REQUEST
    return Response({
        "status": result_status,
        "deleted_count": success_count,
        "deleted_ids": deleted_ids,
        "error_count": len(errors),
        "errors": errors,
    }, status=http_status)


@api_view(["GET"])
def get_scope_statement(request, project_id):
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    email = _resolve_user_email(request)
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED)
    if not _has_scope_statement_access(project, email):
        return _scope_statement_access_denied()

    statement = _statement_for_project(project)
    return Response(_serialize_statement(project, statement, email))


@api_view(["POST"])
@parser_classes([FormParser, MultiPartParser, JSONParser])
def save_scope_statement(request, project_id):
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    email = _resolve_user_email(request)
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED)
    if not _has_scope_statement_access(project, email):
        return _scope_statement_access_denied()

    payload = request.data
    if not isinstance(payload, dict):
        return Response({"error": "Expected JSON object payload."}, status=status.HTTP_400_BAD_REQUEST)

    action = (payload.get("action") or "save").strip().lower()
    if action not in {"save", "lock", "unlock", "submit", "revise"}:
        return Response({"error": "Unsupported action."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        _apply_scope_extensions(ScopeStatement(), payload)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    with transaction.atomic():
        MigrationIntakeSubmission.objects.select_for_update().get(pk=project.pk)
        statement = _statement_for_project(project, for_update=True)
        if statement is None:
            if action != "save":
                return Response({"error": "Save a draft and upload an attachment before locking or submitting."}, status=409)
            statement = ScopeStatement.objects.create(project=project, revision=0)
            for level in JOB_LEVELS:
                ScopeStatementLine.objects.create(statement=statement, job_level=level)
        if "revision" in payload and payload["revision"] != statement.revision:
            return Response({"error": "Scope Statement changed. Reload before saving."}, status=409)

        if action == "revise":
            reason = payload.get("reason", "")
            if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
                return Response({"error": "A revision reason of at most 2000 characters is required."}, status=400)
            if statement.status != "submitted":
                return Response({"error": "Only submitted Scope Statements can be reopened."}, status=409)
            statement.status = "draft"
            statement.audit_log = [*statement.audit_log, {
                "action": "revise", "reason": reason.strip(), "by": email,
                "at": timezone.now().isoformat(),
            }]
            statement.revision += 1
            statement.save()
            return Response(_serialize_statement(project, statement, email))
        if statement.status == "submitted":
            return Response({"error": "Submitted Scope Statement is frozen. Reopen for revision first."}, status=status.HTTP_409_CONFLICT)

        all_lines = list(statement.lines.all())
        page_locked = any(line.locked_at for line in all_lines)
        if action == "unlock":
            if not page_locked:
                return Response({"error": "Scope Statement is already unlocked."}, status=409)
            for line in all_lines:
                line.locked_at = None
                line.locked_by = ""
                line.save(update_fields=["locked_at", "locked_by"])
            statement.revision += 1
            statement.audit_log = [*statement.audit_log, {
                "action": "unlock", "by": email, "at": timezone.now().isoformat(),
                "scope": "page",
            }]
            statement.save()
            return Response(_serialize_statement(project, _statement_for_project(project), email))
        if page_locked and action != "submit":
            return Response({"error": "Scope Statement is locked. Unlock the page before editing."}, status=409)

        scope_text = payload.get("scopeText", statement.scope_text)
        if not isinstance(scope_text, str):
            return Response({"error": "Scope text must be a string."}, status=status.HTTP_400_BAD_REQUEST)
        if page_locked:
            expected = {
                "scopeText": statement.scope_text, "outOfScope": statement.out_of_scope,
                "assumptions": statement.assumptions, "waves": statement.waves,
            }
            if "migratableFte" in payload or "migratableFteConfirmed" in payload:
                return Response({"error": "Unlock the page before changing Migratable FTE."}, status=409)
            if any(key in payload and payload[key] != value for key, value in expected.items()) or payload.get("lines"):
                return Response({"error": "Unlock the page before changing submitted values."}, status=409)
        else:
            statement.scope_text = scope_text[:2000]
            _apply_scope_extensions(statement, payload)
            try:
                _apply_migratable_fte(statement, payload)
            except ValueError as exc:
                return Response({"error": str(exc)}, status=400)

        lines_payload = payload.get("lines")
        changed_lines = []
        if isinstance(lines_payload, list):
            seen = set()
            for row in lines_payload:
                if not isinstance(row, dict) or row.get("jobLevel") not in JOB_LEVELS or row["jobLevel"] in seen:
                    return Response({"error": "Each line must specify a unique valid job level."}, status=400)
                job_level = row.get("jobLevel")
                seen.add(job_level)
                line = next(line for line in all_lines if line.job_level == job_level)
                try:
                    line.agreed_fte = _number(row.get("agreedFte"), f"{job_level} agreed FTE", allow_none=True)
                    line.not_agreed_fte = _number(row.get("notAgreedFte"), f"{job_level} exception FTE", allow_none=True)
                    line.final_fte = _number(row.get("finalFte"), f"{job_level} final FTE", allow_none=True, whole=True)
                except ValueError as exc:
                    return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
                changed_lines.append(line)
        elif lines_payload is not None:
            return Response({"error": "Lines must be a list."}, status=400)

        if action == "lock":
            if statement.migratable_fte is None or not statement.migratable_fte_confirmed:
                return Response({"error": "Manually confirm Migratable FTE before locking the page."}, status=400)
            if not statement.attachments.exists():
                return Response({"error": "Upload an attachment before locking the page."}, status=400)
            if len(all_lines) != 3 or not statement.scope_text.strip() or any(
                line.agreed_fte is None or line.not_agreed_fte is None or line.final_fte is None
                for line in all_lines
            ):
                return Response({"error": "Complete Scope text and all job-level values before locking the page."}, status=400)
            total = sum(line.final_fte for line in all_lines)
            if statement.waves and sum(wave["fte"] for wave in statement.waves) != total:
                return Response({"error": "Migration wave FTE must equal the final project FTE."}, status=400)
            now = timezone.now()
            for line in all_lines:
                line.locked_at = now
                line.locked_by = email
            changed_lines = all_lines
        elif action == "submit":
            if statement.migratable_fte is None or not statement.migratable_fte_confirmed:
                return Response({"error": "Unlock the page and manually confirm Migratable FTE before submitting."}, status=400)
            if not statement.scope_text.strip():
                return Response({"error": "High-level scope statement is required before submitting."}, status=status.HTTP_400_BAD_REQUEST)
            if len(all_lines) != 3 or any(line.locked_at is None for line in all_lines) or not statement.attachments.exists():
                return Response({"error": "Lock the whole page with an attachment before submitting."}, status=status.HTTP_400_BAD_REQUEST)
            statement.ambition_fte = Decimal(str(project.fte_number or 0))
            statement.final_project_fte = sum(int(line.final_fte or 0) for line in all_lines)
            if statement.waves and sum(wave["fte"] for wave in statement.waves) != statement.final_project_fte:
                transaction.set_rollback(True)
                return Response({"error": "Migration wave FTE must equal the locked final project FTE."}, status=400)
            statement.status = "submitted"
            statement.review_required = False
            statement.submitted_at = timezone.now()
            statement.submitted_by = email
        for line in changed_lines:
            line.save()
        statement.revision += 1
        statement.audit_log.append({
            "action": action,
            "by": email,
            "at": timezone.now().isoformat(),
            "scope": "page",
            "migratableFte": str(statement.migratable_fte) if statement.migratable_fte is not None else None,
            "migratableFteConfirmed": statement.migratable_fte_confirmed,
        })
        statement.save()
        statement = _statement_for_project(project)

        return Response(_serialize_statement(project, statement, email))


def _apply_migratable_fte(statement, payload):
    if "migratableFte" in payload:
        value = _number(payload["migratableFte"], "Migratable FTE", allow_none=True)
        if value is not None and value.as_tuple().exponent < -4:
            raise ValueError("Migratable FTE supports at most four decimal places.")
        if value != statement.migratable_fte:
            statement.migratable_fte_confirmed = False
        statement.migratable_fte = value
    if "migratableFteConfirmed" in payload:
        confirmed = payload["migratableFteConfirmed"]
        if not isinstance(confirmed, bool):
            raise ValueError("Migratable FTE confirmation must be true or false.")
        if confirmed and statement.migratable_fte is None:
            raise ValueError("Enter Migratable FTE before confirming.")
        statement.migratable_fte_confirmed = confirmed


def _apply_scope_extensions(statement, payload):
    for key, field in (("outOfScope", "out_of_scope"), ("assumptions", "assumptions")):
        if key in payload:
            value = payload[key]
            if not isinstance(value, str) or len(value) > 10000:
                raise ValueError(f"{key} must be text of at most 10000 characters.")
            setattr(statement, field, value.strip())
    if "waves" not in payload:
        return
    waves = payload["waves"]
    if isinstance(waves, str):
        try:
            waves = json.loads(waves)
        except ValueError:
            raise ValueError("Migration waves must be a JSON list.")
    if not isinstance(waves, list) or len(waves) > 100:
        raise ValueError("At most 100 migration waves are allowed.")
    cleaned = []
    for wave in waves:
        if not isinstance(wave, dict) or set(wave) - {"name", "date", "fte"}:
            raise ValueError("Each wave needs a name, date and FTE.")
        name = wave.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > 255:
            raise ValueError("Wave name is required and must be at most 255 characters.")
        try:
            day = date.fromisoformat(wave.get("date", "")).isoformat()
        except (ValueError, TypeError):
            raise ValueError("Wave date must be YYYY-MM-DD.")
        cleaned.append({"name": name.strip(), "date": day, "fte": _number(wave.get("fte"), "Wave FTE", whole=True)})
    statement.waves = cleaned


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_scope_evidence(request, project_id, job_level=None):
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    email = _resolve_user_email(request)
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED)
    if not _has_scope_statement_access(project, email):
        return _scope_statement_access_denied()

    if job_level is not None and job_level not in JOB_LEVELS:
        return Response({"error": "Unknown job level."}, status=status.HTTP_404_NOT_FOUND)

    uploaded = request.FILES.get("file")
    if uploaded is None:
        return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
    suffix = Path(uploaded.name).suffix.lower()
    if suffix not in EVIDENCE_EXTENSIONS:
        return Response({"error": "Only PDF, DOCX, MSG and XLSX files are accepted."}, status=status.HTTP_400_BAD_REQUEST)
    if uploaded.size <= 0 or uploaded.size > MAX_EVIDENCE_BYTES:
        return Response({"error": "Evidence file must be between 1 byte and 20 MB."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        MigrationIntakeSubmission.objects.select_for_update().get(pk=project.pk)
        statement = _statement_for_project(project, for_update=True)
        if statement is None:
            statement = ScopeStatement.objects.create(project=project)
            for level in JOB_LEVELS:
                ScopeStatementLine.objects.create(statement=statement, job_level=level)
        if "revision" in request.data and str(statement.revision) != str(request.data["revision"]):
            return Response({"error": "Scope Statement changed. Reload before uploading."}, status=409)
        if statement.status == "submitted" or statement.lines.filter(locked_at__isnull=False).exists():
            return Response({"error": "Unlock the Scope Statement before uploading attachments."}, status=409)

        storage_name = f"{uuid4().hex}{suffix}"
        file_entry = ScopeStatementEvidence(
            statement=statement,
            file_name=uploaded.name,
            file_size=uploaded.size,
            uploaded_by=email,
        )
        file_entry.file.save(storage_name, uploaded, save=False)
        file_entry.save()
        statement.revision += 1
        statement.audit_log.append({
            "action": "attach_attachment",
            "by": email,
            "at": timezone.now().isoformat(),
            "file": uploaded.name,
        })
        statement.save()
        statement = _statement_for_project(project)

    return Response(_serialize_statement(project, statement, email), status=status.HTTP_201_CREATED)


@api_view(["GET"])
def download_scope_evidence(request, project_id, evidence_id):
    email = _resolve_user_email(request)
    if not email:
        return Response({"error": "Sign in required. Missing SSO email."}, status=status.HTTP_401_UNAUTHORIZED)
    project = _get_project(project_id)
    if not project:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
    if not _has_scope_statement_access(project, email):
        return _scope_statement_access_denied()

    try:
        evidence = ScopeStatementEvidence.objects.get(
            pk=evidence_id,
            statement__project=project,
        )
    except ScopeStatementEvidence.DoesNotExist:
        return Response({"error": "Evidence not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        handle = evidence.file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("Evidence file is missing from storage.")
    return FileResponse(handle, as_attachment=True, filename=evidence.file_name)
