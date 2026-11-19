from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0071_merge_migration_team_defaults"),
    ]

    operations = [
        migrations.CreateModel(
            name="GscSiteRequest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("site", models.CharField(max_length=128)),
                ("requested_by", models.CharField(max_length=255)),
                ("approver_emails", models.JSONField(default=list)),
                ("request_comment", models.TextField()),
                ("status", models.CharField(db_index=True, default="pending", max_length=16)),
                ("decision_comment", models.TextField(blank=True, default="")),
                ("decided_by", models.CharField(blank=True, default="", max_length=255)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gsc_site_requests",
                        to="api.migrationintakesubmission",
                    ),
                ),
            ],
            options={
                "db_table": "gsc_site_request",
                "ordering": ["-created_at", "id"],
            },
        ),
    ]
