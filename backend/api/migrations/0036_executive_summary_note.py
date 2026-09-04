from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0035_rename_bpm_actual_year_onboarding_idx_bpm_actual_year_5f5bb2_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExecutiveSummaryNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("section", models.CharField(blank=True, default="", max_length=32)),
                ("year", models.PositiveSmallIntegerField(default=0)),
                ("title", models.CharField(blank=True, default="", max_length=64)),
                ("body", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "executive_summary_note",
                "ordering": ["year", "section", "id"],
            },
        ),
        migrations.AddIndex(
            model_name="executivesummarynote",
            index=models.Index(fields=["year", "section"], name="exec_summary_year_section_idx"),
        ),
    ]
