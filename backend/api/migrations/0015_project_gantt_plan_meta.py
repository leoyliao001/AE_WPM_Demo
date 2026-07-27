from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0014_project_gantt_plan"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectganttplan",
            name="meta",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Project summary fields (phase, scope, FTE, HC, totals).",
            ),
        ),
        migrations.AlterField(
            model_name="projectganttplan",
            name="tasks",
            field=models.JSONField(
                default=list,
                help_text="[{id, name, startWeek, endWeek, phaseId}, ...]",
            ),
        ),
    ]
