from django.db import migrations, models


def backfill_super_admin_migration_intake(apps, schema_editor):
    ProjectAttributesAccess = apps.get_model("api", "ProjectAttributesAccess")
    ProjectAttributesAccess.objects.filter(is_super_admin=True).update(
        fpo_mapping=True,
        product_ownership=True,
        gsc_site_mapping=True,
        service_catalogue=True,
        project_gantt=True,
        migration_intake=True,
        access_control=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0019_service_catalogue"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectattributesaccess",
            name="migration_intake",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            backfill_super_admin_migration_intake,
            migrations.RunPython.noop,
        ),
    ]
