from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0016_project_gantt_plan_migration_request_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectattributesaccess",
            name="project_gantt",
            field=models.BooleanField(default=False),
        ),
    ]
