from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0058_opportunity_assessment_system"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicecatalogue",
            name="direction",
            field=models.CharField(blank=True, default="", max_length=16),
        ),
        migrations.AddField(
            model_name="servicecatalogue",
            name="average_handle_time",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="servicecatalogue",
            name="task_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]