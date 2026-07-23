from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0010_rename_oa_volume_and_task_time"),
    ]

    operations = [
        migrations.AddField(
            model_name="productownership",
            name="area",
            field=models.CharField(blank=True, db_index=True, default="", max_length=32),
        ),
        migrations.RemoveIndex(
            model_name="productownership",
            name="product_own_product_4e8731_idx",
        ),
        migrations.RemoveIndex(
            model_name="productownership",
            name="product_own_manager_5530e9_idx",
        ),
        migrations.RemoveField(
            model_name="productownership",
            name="product",
        ),
        migrations.RemoveField(
            model_name="productownership",
            name="manager",
        ),
        migrations.AddIndex(
            model_name="productownership",
            index=models.Index(fields=["region", "area"], name="product_own_region_5f2a1c_idx"),
        ),
        migrations.AddIndex(
            model_name="productownership",
            index=models.Index(fields=["migration_manager"], name="product_own_migrati_8d4b2e_idx"),
        ),
    ]
