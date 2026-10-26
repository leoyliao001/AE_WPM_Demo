from django.db import migrations, models


def grant_existing_stakeholder_registration_access(apps, schema_editor):
    ProjectAttributesAccess = apps.get_model("api", "ProjectAttributesAccess")
    ProjectAttributesAccess.objects.using(schema_editor.connection.alias).all().update(
        stakeholder_registration=True
    )


def reverse_stakeholder_registration_access(apps, schema_editor):
    ProjectAttributesAccess = apps.get_model("api", "ProjectAttributesAccess")
    ProjectAttributesAccess.objects.using(schema_editor.connection.alias).all().update(
        stakeholder_registration=False
    )


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0046_stakeholder_registration"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectattributesaccess",
            name="stakeholder_registration",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            grant_existing_stakeholder_registration_access,
            reverse_stakeholder_registration_access,
        ),
    ]