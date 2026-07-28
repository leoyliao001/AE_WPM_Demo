from django.db import migrations


def backfill_super_admin_project_gantt(apps, schema_editor):
    ProjectAttributesAccess = apps.get_model("api", "ProjectAttributesAccess")
    ProjectAttributesAccess.objects.filter(is_super_admin=True).update(
        fpo_mapping=True,
        product_ownership=True,
        gsc_site_mapping=True,
        project_gantt=True,
        access_control=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0017_project_attributes_access_project_gantt"),
    ]

    operations = [
        migrations.RunPython(backfill_super_admin_project_gantt, migrations.RunPython.noop),
    ]
