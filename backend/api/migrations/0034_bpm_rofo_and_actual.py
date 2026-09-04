from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0033_approvalworkflow_wpm_approved_by"),
    ]

    operations = [
        migrations.CreateModel(
            name="BpmRofo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("project_name", models.CharField(blank=True, default="", max_length=255)),
                ("product", models.CharField(blank=True, default="", max_length=255)),
                ("region", models.CharField(blank=True, default="", max_length=64)),
                ("area", models.CharField(blank=True, default="", max_length=128)),
                ("onboarding_month", models.CharField(blank=True, default="", max_length=32)),
                ("year", models.PositiveSmallIntegerField(default=0)),
                ("bpm_owner", models.CharField(blank=True, default="", max_length=255)),
                ("rofo_value", models.CharField(blank=True, default="", max_length=64)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "bpm_rofo",
                "ordering": ["-year", "project_name", "id"],
            },
        ),
        migrations.CreateModel(
            name="BpmActual",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("project_name", models.CharField(blank=True, default="", max_length=255)),
                ("product", models.CharField(blank=True, default="", max_length=255)),
                ("region", models.CharField(blank=True, default="", max_length=64)),
                ("area", models.CharField(blank=True, default="", max_length=128)),
                ("onboarding_month", models.CharField(blank=True, default="", max_length=32)),
                ("year", models.PositiveSmallIntegerField(default=0)),
                ("bpm_owner", models.CharField(blank=True, default="", max_length=255)),
                ("actual_value", models.CharField(blank=True, default="", max_length=64)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "bpm_actual",
                "ordering": ["-year", "project_name", "id"],
            },
        ),
        migrations.AddField(
            model_name="projectattributesaccess",
            name="bpm_rofo",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="projectattributesaccess",
            name="bpm_actual",
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name="bpmrofo",
            index=models.Index(fields=["year", "onboarding_month"], name="bpm_rofo_year_onboarding_idx"),
        ),
        migrations.AddIndex(
            model_name="bpmrofo",
            index=models.Index(fields=["project_name"], name="bpm_rofo_project_name_idx"),
        ),
        migrations.AddIndex(
            model_name="bpmactual",
            index=models.Index(fields=["year", "onboarding_month"], name="bpm_actual_year_onboarding_idx"),
        ),
        migrations.AddIndex(
            model_name="bpmactual",
            index=models.Index(fields=["project_name"], name="bpm_actual_project_name_idx"),
        ),
    ]
