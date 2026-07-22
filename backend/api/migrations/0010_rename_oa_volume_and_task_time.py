from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_rename_gsc_site_ma_region_8a2c1f_idx_gsc_site_ma_region_5b7743_idx_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="opportunityassessment",
            old_name="volume",
            new_name="volume_monthly",
        ),
        migrations.RenameField(
            model_name="opportunityassessment",
            old_name="task_time_per_unit",
            new_name="task_time_per_unit_min",
        ),
    ]
