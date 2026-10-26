from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0045_alter_projectattributesaccess_scope_statement_default"),
    ]

    operations = [
        migrations.CreateModel(
            name="StakeholderRegistration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("team_members", models.JSONField(default=list)),
                ("assignments", models.JSONField(default=dict)),
                ("audit_log", models.JSONField(default=list)),
                ("revision", models.PositiveIntegerField(default=0)),
                ("updated_by", models.CharField(blank=True, default="", max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stakeholder_registration",
                        to="api.migrationintakesubmission",
                    ),
                ),
            ],
            options={"db_table": "stakeholder_registration"},
        ),
    ]