from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0074_remove_migrationintakesubmission_risks"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="migrationintakesubmission",
            name="job_level_total",
        ),
        migrations.RemoveField(
            model_name="migrationintakesubmission",
            name="jl2",
        ),
        migrations.RemoveField(
            model_name="migrationintakesubmission",
            name="jl3",
        ),
        migrations.RemoveField(
            model_name="migrationintakesubmission",
            name="jl4",
        ),
    ]
