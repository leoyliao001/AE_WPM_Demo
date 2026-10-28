from django.db import migrations, models
import django.db.models.deletion


def link_existing_attachments(apps, schema_editor):
    Evidence = apps.get_model("api", "ScopeStatementEvidence")
    for evidence in Evidence.objects.using(schema_editor.connection.alias).select_related("line").all():
        evidence.statement_id = evidence.line.statement_id
        evidence.save(using=schema_editor.connection.alias, update_fields=["statement"])


class Migration(migrations.Migration):
    dependencies = [("api", "0051_business_case_saved_snapshot")]

    operations = [
        migrations.AddField(
            model_name="scopestatementevidence", name="statement",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name="attachments", to="api.scopestatement"),
        ),
        migrations.RunPython(link_existing_attachments, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="scopestatementevidence", name="statement",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name="attachments", to="api.scopestatement"),
        ),
        migrations.AlterField(
            model_name="scopestatementevidence", name="line",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name="evidence", to="api.scopestatementline"),
        ),
    ]
