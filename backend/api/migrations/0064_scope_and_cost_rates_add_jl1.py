from django.db import migrations, models


def backfill_jl1_scope_lines(apps, schema_editor):
    ScopeStatement = apps.get_model("api", "ScopeStatement")
    ScopeStatementLine = apps.get_model("api", "ScopeStatementLine")
    database = schema_editor.connection.alias

    for statement in ScopeStatement.objects.using(database).all().iterator():
        lines = list(ScopeStatementLine.objects.using(database).filter(statement_id=statement.pk))
        if any(line.job_level == "JL1" for line in lines):
            continue

        locked_lines = [line for line in lines if line.locked_at and line.final_fte is not None]
        page_was_locked = len(locked_lines) == 3 and statement.status in {"draft", "submitted"}
        ScopeStatementLine.objects.using(database).create(
            statement_id=statement.pk,
            job_level="JL1",
            agreed_fte=0 if page_was_locked else None,
            not_agreed_fte=0 if page_was_locked else None,
            final_fte=0 if page_was_locked else None,
            locked_at=locked_lines[0].locked_at if page_was_locked else None,
            locked_by=locked_lines[0].locked_by if page_was_locked else "",
        )


class Migration(migrations.Migration):
    dependencies = [("api", "0063_gantt_remove_completed_at")]

    operations = [
        migrations.AlterField(
            model_name="scopestatementline",
            name="job_level",
            field=models.CharField(
                choices=[("JL1", "JL1"), ("JL2", "JL2"), ("JL3", "JL3"), ("JL4", "JL4")],
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="businesscasecostrate",
            name="job_level",
            field=models.CharField(
                choices=[("JL1", "JL1"), ("JL2", "JL2"), ("JL3", "JL3"), ("JL4", "JL4")],
                max_length=3,
            ),
        ),
        migrations.RunPython(backfill_jl1_scope_lines, migrations.RunPython.noop),
    ]