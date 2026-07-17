from django.db import migrations, models


def mark_existing_as_reference(apps, schema_editor):
    FpoMapping = apps.get_model("api", "FpoMapping")
    FpoMapping.objects.all().update(is_reference=True)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_fpo_mapping"),
    ]

    operations = [
        migrations.AddField(
            model_name="fpomapping",
            name="is_reference",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="True = Excel dictionary row for cascade dropdowns only; not shown in the grid.",
            ),
        ),
        migrations.RunPython(mark_existing_as_reference, migrations.RunPython.noop),
    ]
