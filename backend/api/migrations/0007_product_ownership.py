import json
from pathlib import Path

from django.db import migrations, models


def seed_product_ownership(apps, schema_editor):
    ProductOwnership = apps.get_model("api", "ProductOwnership")
    if ProductOwnership.objects.exists():
        return

    seed_path = Path(__file__).resolve().parent.parent / "data" / "product_ownership_seed.json"
    if not seed_path.exists():
        return

    rows = json.loads(seed_path.read_text(encoding="utf-8"))
    ProductOwnership.objects.bulk_create(
        [
            ProductOwnership(
                product=row.get("product", ""),
                manager=row.get("manager", ""),
                region=row.get("region", ""),
                migration_manager=row.get("migration_manager", ""),
            )
            for row in rows
            if isinstance(row, dict)
        ]
    )


def unseed_product_ownership(apps, schema_editor):
    ProductOwnership = apps.get_model("api", "ProductOwnership")
    ProductOwnership.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0006_opportunity_assessment"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductOwnership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product", models.CharField(blank=True, default="", max_length=255)),
                ("manager", models.CharField(blank=True, default="", max_length=128)),
                ("region", models.CharField(blank=True, db_index=True, default="", max_length=16)),
                ("migration_manager", models.CharField(blank=True, default="", max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "product_ownership",
                "ordering": ["id"],
            },
        ),
        migrations.AddIndex(
            model_name="productownership",
            index=models.Index(fields=["product", "region"], name="product_own_product_7c9f2a_idx"),
        ),
        migrations.AddIndex(
            model_name="productownership",
            index=models.Index(fields=["manager"], name="product_own_manager_4e1b8d_idx"),
        ),
        migrations.RunPython(seed_product_ownership, unseed_product_ownership),
    ]
