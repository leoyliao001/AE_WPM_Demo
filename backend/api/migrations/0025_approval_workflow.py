from django.db import migrations, models


def backfill_super_admin_approval_workflow(apps, schema_editor):
    ProjectAttributesAccess = apps.get_model("api", "ProjectAttributesAccess")
    ProjectAttributesAccess.objects.filter(is_super_admin=True).update(
        fpo_mapping=True,
        product_ownership=True,
        gsc_site_mapping=True,
        service_catalogue=True,
        working_hours=True,
        project_gantt=True,
        migration_intake=True,
        approval_workflow=True,
        access_control=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0024_working_hours"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApprovalWorkflow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("migration_request_id", models.CharField(db_index=True, max_length=32, unique=True)),
                ("business_case_submitted_date", models.DateTimeField(blank=True, null=True)),
                ("area_head_approval_trigger_date", models.DateTimeField(blank=True, null=True)),
                ("area_head_comments", models.TextField(blank=True, default="")),
                ("area_head_final_date", models.DateTimeField(blank=True, null=True)),
                ("area_head_status", models.CharField(blank=True, default="", max_length=64)),
                ("pmo_review_comment", models.TextField(blank=True, default="")),
                ("pmo_review_date", models.DateTimeField(blank=True, null=True)),
                ("pmo_status", models.CharField(blank=True, default="", max_length=64)),
                ("bpm_budget_status", models.CharField(blank=True, default="", max_length=64)),
                ("bpm_comment", models.TextField(blank=True, default="")),
                ("bpm_review_date", models.DateTimeField(blank=True, null=True)),
                ("fbp_review_date", models.DateTimeField(blank=True, null=True)),
                ("fbp_comment", models.TextField(blank=True, default="")),
                ("fbp_status", models.CharField(blank=True, default="", max_length=64)),
                ("wpm_review_date", models.DateTimeField(blank=True, null=True)),
                ("wpm_review_comment", models.TextField(blank=True, default="")),
                ("wpm_review_status", models.CharField(blank=True, default="", max_length=64)),
                ("gsc_head_date", models.DateTimeField(blank=True, null=True)),
                ("gsc_head_comment", models.TextField(blank=True, default="")),
                ("gsc_head_status", models.CharField(blank=True, default="", max_length=64)),
                ("elt_date", models.DateTimeField(blank=True, null=True)),
                ("elt_comment", models.TextField(blank=True, default="")),
                ("elt_status", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "approval_workflow",
                "ordering": ["-updated_at", "id"],
            },
        ),
        migrations.AddField(
            model_name="projectattributesaccess",
            name="approval_workflow",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(backfill_super_admin_approval_workflow, migrations.RunPython.noop),
    ]
