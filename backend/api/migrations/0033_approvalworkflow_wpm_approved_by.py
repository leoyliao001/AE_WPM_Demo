from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api", "0032_approvalworkflow_approver_emails")]

    operations = [
        migrations.AddField(
            model_name="approvalworkflow",
            name="wpm_approved_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]