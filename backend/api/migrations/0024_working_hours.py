import json
from pathlib import Path

from django.db import migrations, models


def seed_working_hours(apps, schema_editor):
    WorkingHours = apps.get_model("api", "WorkingHours")
    if WorkingHours.objects.exists():
        return

    seed_path = Path(__file__).resolve().parent.parent / "data" / "working_hours_seed.json"
    if not seed_path.exists():
        return

    rows = json.loads(seed_path.read_text(encoding="utf-8"))
    WorkingHours.objects.bulk_create(
        [
            WorkingHours(
                area=row.get("area", ""),
                aera_working_hours=row.get("aera_working_hours", ""),
                gsc=row.get("gsc", ""),
                gsc_working_hours=row.get("gsc_working_hours", ""),
            )
            for row in rows
            if isinstance(row, dict)
        ]
    )


def unseed_working_hours(apps, schema_editor):
    WorkingHours = apps.get_model("api", "WorkingHours")
    WorkingHours.objects.all().delete()


def backfill_super_admin_working_hours(apps, schema_editor):
    ProjectAttributesAccess = apps.get_model("api", "ProjectAttributesAccess")
    ProjectAttributesAccess.objects.filter(is_super_admin=True).update(
        fpo_mapping=True,
        product_ownership=True,
        gsc_site_mapping=True,
        service_catalogue=True,
        working_hours=True,
        project_gantt=True,
        migration_intake=True,
        access_control=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0023_alter_projectganttplan_tasks"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkingHours",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("area", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                ("aera_working_hours", models.CharField(blank=True, default="", max_length=32)),
                ("gsc", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                ("gsc_working_hours", models.CharField(blank=True, default="", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "working_hours",
                "ordering": ["id"],
            },
        ),
        migrations.AddIndex(
            model_name="workinghours",
            index=models.Index(fields=["area", "gsc"], name="working_hou_area_gsc_idx"),
        ),
        migrations.AddField(
            model_name="projectattributesaccess",
            name="working_hours",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(seed_working_hours, unseed_working_hours),
        migrations.RunPython(backfill_super_admin_working_hours, migrations.RunPython.noop),
    ]
