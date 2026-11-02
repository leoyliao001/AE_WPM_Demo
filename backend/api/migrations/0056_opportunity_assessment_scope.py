from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("api", "0055_business_impact_analysis")]

    operations = [
        migrations.AddField(
            model_name="opportunityassessment", name="scope_details",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name="OpportunityAssessmentScope",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("state", models.JSONField(default=dict)),
                ("revision", models.PositiveIntegerField(default=0)),
                ("updated_by", models.CharField(blank=True, default="", max_length=254)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="task_scope", to="api.migrationintakesubmission")),
            ],
            options={"db_table": "opportunity_assessment_scope"},
        ),
    ]