# Manually created: change migration_manager max_length 128 -> 255 to store email addresses.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0025_approval_workflow"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productownership",
            name="migration_manager",
            field=models.CharField(
                blank=True,
                default="",
                max_length=255,
                help_text="Email address(es) of the migration manager(s). Comma-separate multiple emails.",
            ),
        ),
    ]
