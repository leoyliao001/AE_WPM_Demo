import json
from pathlib import Path

from django.db import migrations, models


def seed_approval_input(apps, schema_editor):
    ApprovalInput = apps.get_model("api", "ApprovalInput")
    if ApprovalInput.objects.exists():
        return
    seed_path = Path(__file__).resolve().parent.parent / "data" / "approval_input_seed.json"
    if not seed_path.exists():
        return
    rows = json.loads(seed_path.read_text(encoding="utf-8"))
    ApprovalInput.objects.bulk_create([
        ApprovalInput(
            activity_function=row.get("activity_function", ""),
            product=row.get("product", ""),
            area_head=row.get("area_head", ""),
            pmo=row.get("pmo", ""),
            bpm=row.get("bpm", ""),
            fbp=row.get("fbp", ""),
            wpm=row.get("wpm", ""),
            elt=row.get("elt", ""),
            gsc_head=row.get("gsc_head", ""),
        )
        for row in rows if isinstance(row, dict)
    ])


def unseed_approval_input(apps, schema_editor):
    apps.get_model("api", "ApprovalInput").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0026_product_ownership_email"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApprovalInput",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("activity_function", models.CharField(blank=True, default="", max_length=128, db_index=True)),
                ("product", models.CharField(blank=True, default="", max_length=128, db_index=True)),
                ("area_head", models.CharField(blank=True, default="", max_length=255, help_text="Area Head email(s).")),
                ("pmo", models.CharField(blank=True, default="", max_length=255, help_text="PMO email(s).")),
                ("bpm", models.CharField(blank=True, default="", max_length=255, help_text="BPM email(s).")),
                ("fbp", models.CharField(blank=True, default="", max_length=255, help_text="FBP email(s).")),
                ("wpm", models.CharField(blank=True, default="", max_length=255, help_text="WPM email(s).")),
                ("elt", models.CharField(blank=True, default="", max_length=255, help_text="ELT email(s).")),
                ("gsc_head", models.CharField(blank=True, default="", max_length=255, help_text="GSC Head email(s).")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "approval_input",
                "ordering": ["activity_function", "product"],
            },
        ),
        migrations.AddIndex(
            model_name="approvalinput",
            index=models.Index(fields=["activity_function", "product"], name="approval_in_act_fun_idx"),
        ),
        migrations.RunPython(seed_approval_input, unseed_approval_input),
    ]
