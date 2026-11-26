import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0076_remove_scopestatement_waves"),
    ]

    operations = [
        migrations.CreateModel(
            name="LessonLearnt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("happened", models.TextField()),
                ("learned", models.TextField()),
                ("next_time", models.TextField()),
                ("lesson_type", models.CharField(choices=[("Repeat", "Repeat"), ("Improve", "Improve"), ("Avoid", "Avoid"), ("Adopt", "Adopt")], max_length=16)),
                ("phase", models.CharField(choices=[("Initiate", "Initiate"), ("Plan", "Plan"), ("Execute", "Execute"), ("Monitor & Control", "Monitor & Control"), ("Close", "Close")], max_length=32)),
                ("related_artefact", models.CharField(choices=[("Opportunity Assessment", "Opportunity Assessment"), ("Scope Statement", "Scope Statement"), ("Business Case", "Business Case"), ("Resources", "Resources"), ("Safety & Resilience", "Safety & Resilience"), ("Gantt", "Gantt"), ("Knowledge Transfer", "Knowledge Transfer"), ("Hypercare", "Hypercare"), ("Sign-off", "Sign-off"), ("Benefit Realisation", "Benefit Realisation")], max_length=64)),
                ("relevant_for", models.CharField(choices=[("This migration", "This migration"), ("Similar migrations", "Similar migrations"), ("All WPM migrations", "All WPM migrations")], max_length=32)),
                ("created_by", models.CharField(blank=True, default="", max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons_learnt", to="api.migrationintakesubmission")),
            ],
            options={
                "db_table": "lessons_learnt",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
