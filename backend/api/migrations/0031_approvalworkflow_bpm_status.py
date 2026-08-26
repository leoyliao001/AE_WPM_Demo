from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0030_restore_approval_input"),
    ]

    operations = [
        migrations.AddField(
            model_name="approvalworkflow",
            name="bpm_status",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
