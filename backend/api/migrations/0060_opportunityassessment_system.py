from django.db import migrations, models


def add_system_column_if_missing(apps, schema_editor):
    model = apps.get_model("api", "OpportunityAssessment")
    table_name = model._meta.db_table
    with schema_editor.connection.cursor() as cursor:
        columns = schema_editor.connection.introspection.get_table_description(cursor, table_name)
    if any(column.name.casefold() == "system" for column in columns):
        return

    field = models.TextField(blank=True, default="")
    field.set_attributes_from_name("system")
    field.model = model
    schema_editor.add_field(model, field)


class Migration(migrations.Migration):
    dependencies = [("api", "0059_fpo_catalogue_request_comment")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_system_column_if_missing, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="opportunityassessment",
                    name="system",
                    field=models.TextField(blank=True, default=""),
                ),
            ],
        ),
    ]
