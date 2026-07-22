import json
from pathlib import Path

from django.db import migrations, models


def seed_gsc_site_mapping(apps, schema_editor):
    GscSiteMapping = apps.get_model("api", "GscSiteMapping")
    if GscSiteMapping.objects.exists():
        return

    seed_path = Path(__file__).resolve().parent.parent / "data" / "gsc_site_mapping_seed.json"
    if not seed_path.exists():
        return

    rows = json.loads(seed_path.read_text(encoding="utf-8"))
    GscSiteMapping.objects.bulk_create(
        [
            GscSiteMapping(
                region=row.get("region", ""),
                area=row.get("area", ""),
                supporting_gsc_sites=row.get("supporting_gsc_sites", ""),
                all_options=row.get("all_options", ""),
            )
            for row in rows
            if isinstance(row, dict)
        ]
    )


def unseed_gsc_site_mapping(apps, schema_editor):
    GscSiteMapping = apps.get_model("api", "GscSiteMapping")
    GscSiteMapping.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0007_product_ownership"),
    ]

    operations = [
        migrations.CreateModel(
            name="GscSiteMapping",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("region", models.CharField(blank=True, db_index=True, default="", max_length=16)),
                ("area", models.CharField(blank=True, db_index=True, default="", max_length=32)),
                ("supporting_gsc_sites", models.CharField(blank=True, default="", max_length=255)),
                ("all_options", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "gsc_site_mapping",
                "ordering": ["id"],
            },
        ),
        migrations.AddIndex(
            model_name="gscsitemapping",
            index=models.Index(fields=["region", "area"], name="gsc_site_ma_region_8a2c1f_idx"),
        ),
        migrations.RunPython(seed_gsc_site_mapping, unseed_gsc_site_mapping),
    ]
