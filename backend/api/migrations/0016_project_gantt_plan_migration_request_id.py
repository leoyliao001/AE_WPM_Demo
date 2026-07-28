from django.db import migrations, models


def backfill_migration_request_id(apps, schema_editor):
    ProjectGanttPlan = apps.get_model("api", "ProjectGanttPlan")
    for plan in ProjectGanttPlan.objects.select_related("project").all():
        mid = getattr(plan.project, "migration_request_id", "") or ""
        if plan.migration_request_id != mid:
            plan.migration_request_id = mid
            plan.save(update_fields=["migration_request_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0015_project_gantt_plan_meta"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectganttplan",
            name="migration_request_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="Denormalized Migration Request ID (e.g. WPM_PRJ_...) for easier lookup.",
                max_length=32,
            ),
        ),
        migrations.RunPython(backfill_migration_request_id, migrations.RunPython.noop),
    ]
