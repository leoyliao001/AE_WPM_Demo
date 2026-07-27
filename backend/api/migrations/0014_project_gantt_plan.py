from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0013_project_attributes_access"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectGanttPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "tasks",
                    models.JSONField(
                        default=list,
                        help_text="[{id, name, startWeek, endWeek}, ...]",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gantt_plan",
                        to="api.migrationintakesubmission",
                    ),
                ),
            ],
            options={
                "db_table": "project_gantt_plan",
            },
        ),
    ]
