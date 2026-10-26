from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0042_alter_bpmactual_pid_alter_bpmrofo_pid"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScopeStatement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope_text", models.TextField(blank=True, default="")),
                ("status", models.CharField(default="draft", max_length=16)),
                ("revision", models.PositiveIntegerField(default=0)),
                ("ambition_fte", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("final_project_fte", models.PositiveIntegerField(blank=True, null=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("submitted_by", models.CharField(blank=True, default="", max_length=254)),
                ("audit_log", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scope_statement",
                        to="api.migrationintakesubmission",
                    ),
                ),
            ],
            options={"db_table": "scope_statement"},
        ),
        migrations.CreateModel(
            name="ScopeStatementLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("job_level", models.CharField(choices=[("JL2", "JL2"), ("JL3", "JL3"), ("JL4", "JL4")], max_length=3)),
                ("agreed_fte", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("not_agreed_fte", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True)),
                ("final_fte", models.PositiveIntegerField(blank=True, null=True)),
                ("locked_at", models.DateTimeField(blank=True, null=True)),
                ("locked_by", models.CharField(blank=True, default="", max_length=254)),
                (
                    "statement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="api.scopestatement",
                    ),
                ),
            ],
            options={
                "db_table": "scope_statement_line",
                "ordering": ["job_level"],
            },
        ),
        migrations.AddConstraint(
            model_name="scopestatementline",
            constraint=models.UniqueConstraint(fields=("statement", "job_level"), name="scope_unique_job_level"),
        ),
        migrations.CreateModel(
            name="ScopeStatementEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(max_length=255, upload_to="scope_evidence/%Y/%m/")),
                ("file_name", models.CharField(max_length=255)),
                ("file_size", models.PositiveIntegerField()),
                ("uploaded_by", models.CharField(max_length=254)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "line",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evidence",
                        to="api.scopestatementline",
                    ),
                ),
            ],
            options={"db_table": "scope_statement_evidence", "ordering": ["id"]},
        ),
    ]
