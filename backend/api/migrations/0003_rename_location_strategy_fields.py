from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0002_consolidate_to_single_table"),
    ]

    operations = [
        migrations.RenameField(
            model_name="migrationintakesubmission",
            old_name="default_supporting_gsc_sites",
            new_name="default_location_strategies",
        ),
        migrations.RenameField(
            model_name="migrationintakesubmission",
            old_name="custom_supporting_gsc_sites",
            new_name="custom_location_strategies",
        ),
        migrations.RenameField(
            model_name="migrationintakesubmission",
            old_name="supporting_gsc_sites_custom",
            new_name="location_strategy_custom",
        ),
        migrations.RenameField(
            model_name="migrationintakesubmission",
            old_name="custom_supporting_justification",
            new_name="custom_location_strategy_justification",
        ),
        migrations.RemoveField(
            model_name="migrationintakesubmission",
            name="location_strategies",
        ),
        migrations.RemoveField(
            model_name="migrationintakesubmission",
            name="area_location_pairs",
        ),
    ]
