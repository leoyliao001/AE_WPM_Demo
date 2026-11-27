from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0082_remove_weekly_kpi_comments"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectattributesaccess",
            name="baseline_kpis",
            field=models.BooleanField(default=False),
        ),
    ]
