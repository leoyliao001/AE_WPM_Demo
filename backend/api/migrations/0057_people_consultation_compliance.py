from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0056_opportunity_assessment_scope"),
    ]

    operations = [
        migrations.CreateModel(
            name="PeopleConsultationCompliance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("items", models.JSONField(default=list)),
                ("status", models.CharField(default="draft", max_length=16)),
                ("version", models.PositiveIntegerField(default=0)),
                ("revision", models.PositiveIntegerField(default=0)),
                ("audit_log", models.JSONField(default=list)),
                ("updated_by", models.CharField(blank=True, default="", max_length=254)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="people_consultation_compliance",
                    to="api.migrationintakesubmission",
                )),
            ],
            options={"db_table": "people_consultation_compliance"},
        ),
        migrations.CreateModel(
            name="PeopleConsultationEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item_id", models.CharField(max_length=80)),
                ("file", models.FileField(upload_to="people-consultation/%Y/%m/")),
                ("original_name", models.CharField(max_length=255)),
                ("size", models.PositiveIntegerField(default=0)),
                ("uploaded_by", models.CharField(blank=True, default="", max_length=254)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="people_consultation_evidence",
                    to="api.migrationintakesubmission",
                )),
            ],
            options={
                "db_table": "people_consultation_evidence",
                "ordering": ["uploaded_at", "id"],
            },
        ),
    ]
