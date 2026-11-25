from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0075_remove_migrationintakesubmission_job_level_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="scopestatement",
            name="waves",
        ),
    ]
