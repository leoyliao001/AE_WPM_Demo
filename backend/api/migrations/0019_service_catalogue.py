import json
from pathlib import Path

from django.db import migrations, models


def seed_service_catalogue(apps, schema_editor):
    ServiceCatalogue = apps.get_model("api", "ServiceCatalogue")
    if ServiceCatalogue.objects.exists():
        return

    seed_path = Path(__file__).resolve().parent.parent / "data" / "service_catalogue_seed.json"
    if not seed_path.exists():
        return

    rows = json.loads(seed_path.read_text(encoding="utf-8"))
    ServiceCatalogue.objects.bulk_create(
        [
            ServiceCatalogue(
                catalogue=row.get("catalogue", ""),
                product=row.get("product", ""),
                l1=row.get("l1", ""),
                l2=row.get("l2", ""),
                l3=row.get("l3", ""),
                l4=row.get("l4", ""),
                current_ownership=row.get("current_ownership", ""),
                customer=row.get("customer", ""),
            )
            for row in rows
            if isinstance(row, dict)
        ]
    )


def unseed_service_catalogue(apps, schema_editor):
    ServiceCatalogue = apps.get_model("api", "ServiceCatalogue")
    ServiceCatalogue.objects.all().delete()


def backfill_super_admin_service_catalogue(apps, schema_editor):
    ProjectAttributesAccess = apps.get_model("api", "ProjectAttributesAccess")
    ProjectAttributesAccess.objects.filter(is_super_admin=True).update(
        fpo_mapping=True,
        product_ownership=True,
        gsc_site_mapping=True,
        service_catalogue=True,
        project_gantt=True,
        access_control=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0018_backfill_super_admin_project_gantt"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceCatalogue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("catalogue", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                ("product", models.CharField(blank=True, db_index=True, default="", max_length=128)),
                ("l1", models.CharField(blank=True, db_index=True, default="", max_length=128)),
                ("l2", models.CharField(blank=True, default="", max_length=128)),
                ("l3", models.CharField(blank=True, default="", max_length=128)),
                ("l4", models.CharField(blank=True, default="", max_length=255)),
                ("current_ownership", models.CharField(blank=True, default="", max_length=64)),
                ("customer", models.CharField(blank=True, default="", max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "service_catalogue",
                "ordering": ["id"],
            },
        ),
        migrations.AddIndex(
            model_name="servicecatalogue",
            index=models.Index(
                fields=["product", "l1", "l2", "l3"],
                name="service_cat_product_l123_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="servicecatalogue",
            index=models.Index(
                fields=["current_ownership"],
                name="service_cat_ownership_idx",
            ),
        ),
        migrations.AddField(
            model_name="projectattributesaccess",
            name="service_catalogue",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(seed_service_catalogue, unseed_service_catalogue),
        migrations.RunPython(backfill_super_admin_service_catalogue, migrations.RunPython.noop),
    ]
