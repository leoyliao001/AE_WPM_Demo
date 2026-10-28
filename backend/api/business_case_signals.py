from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from api.models import BusinessCase, BusinessCaseCostRate, MigrationIntakeSubmission, ScopeStatement, ScopeStatementLine
from api.services.business_case import INTAKE_FIELDS, build_business_case


@receiver(pre_save, sender=MigrationIntakeSubmission)
@receiver(pre_save, sender=ScopeStatement)
@receiver(pre_save, sender=ScopeStatementLine)
@receiver(pre_save, sender=BusinessCaseCostRate)
def capture_source_change(sender, instance, raw=False, **kwargs):
    if raw:
        return
    fields = {
        MigrationIntakeSubmission: INTAKE_FIELDS,
        ScopeStatement: ("scope_text", "out_of_scope", "assumptions", "waves", "status", "final_project_fte", "review_required", "migratable_fte", "migratable_fte_confirmed"),
        ScopeStatementLine: ("final_fte", "locked_at"),
        BusinessCaseCostRate: ("location", "job_level", "annual_cost", "currency", "usd_rate", "year", "version"),
    }[sender]
    previous = sender.objects.filter(pk=instance.pk).values(*fields).first() if instance.pk else None
    instance._business_case_source_changes = {
        field: {"old": previous[field] if previous else None, "new": getattr(instance, field)}
        for field in fields if not previous or previous[field] != getattr(instance, field)
    }
    instance._business_case_source_changed = previous is None or any(previous[field] != getattr(instance, field) for field in fields)


@receiver(post_save, sender=MigrationIntakeSubmission)
@receiver(post_save, sender=ScopeStatement)
@receiver(post_save, sender=ScopeStatementLine)
@receiver(post_save, sender=BusinessCaseCostRate)
@receiver(post_delete, sender=ScopeStatement)
@receiver(post_delete, sender=ScopeStatementLine)
@receiver(post_delete, sender=BusinessCaseCostRate)
def flag_changed_business_cases(sender, instance, raw=False, **kwargs):
    if raw or (kwargs.get("signal") is not post_delete and getattr(instance, "_business_case_source_changed", True) is False):
        return
    if sender is MigrationIntakeSubmission:
        scope_fields = {
            "migration_type", "function_name", "products", "countries", "default_location_strategies",
            "custom_location_strategies", "location_strategy_custom", "target_start_date", "target_end_date",
        }
        changes = getattr(instance, "_business_case_source_changes", {})
        if scope_fields.intersection(changes):
            statement = ScopeStatement.objects.filter(project=instance, status="submitted", review_required=False).first()
            if statement:
                ScopeStatement.objects.filter(pk=statement.pk).update(
                    review_required=True,
                    revision=statement.revision + 1,
                    updated_at=timezone.now(),
                    audit_log=[*statement.audit_log, {
                        "action": "intake_changed", "at": timezone.now().isoformat(),
                        "fields": sorted(scope_fields.intersection(changes)),
                        "reason": "Intake scope inputs changed. Review and resubmit Scope.",
                    }],
                )
    cases = BusinessCase.objects.filter(status="submitted", review_required=False).select_related("project")
    if sender is MigrationIntakeSubmission:
        cases = cases.filter(project_id=instance.pk)
    elif sender is ScopeStatement:
        cases = cases.filter(project_id=instance.project_id)
    elif sender is ScopeStatementLine:
        cases = cases.filter(project__scope_statement__pk=instance.statement_id)
    for record in cases:
        fingerprint = build_business_case(record.project, record)[3]
        if record.source_fingerprint == fingerprint:
            continue
        at = timezone.now()
        entry = {"action": "source_changed", "source": sender._meta.db_table,
                 "at": at.isoformat(), "reason": "Upstream data changed; reopen and resubmit for approval.",
                 "changes": {
                     key: {side: str(value) for side, value in values.items()}
                     for key, values in getattr(instance, "_business_case_source_changes", {}).items()
                 }}
        BusinessCase.objects.filter(pk=record.pk, review_required=False).update(
            review_required=True, revision=record.revision + 1,
            audit_log=[*record.audit_log, entry], updated_at=at,
        )
