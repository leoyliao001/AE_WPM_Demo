from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_fpo_mapping_is_reference"),
    ]

    operations = [
        migrations.CreateModel(
            name="OpportunityAssessment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("migration_request_id", models.CharField(db_index=True, max_length=32)),
                ("owner", models.CharField(blank=True, default="", max_length=128)),
                ("l1", models.CharField(blank=True, default="", max_length=128)),
                ("l2", models.CharField(blank=True, default="", max_length=128)),
                ("l3", models.CharField(blank=True, default="", max_length=128)),
                ("l4", models.CharField(blank=True, default="", max_length=255)),
                ("task_name", models.CharField(blank=True, default="", max_length=255)),
                ("task_description", models.TextField(blank=True, default="")),
                ("task_found_in_service_catalog", models.CharField(blank=True, default="", max_length=255)),
                ("migratable_to_gsc", models.CharField(blank=True, default="", max_length=255)),
                ("upstream", models.TextField(blank=True, default="")),
                ("downstream", models.TextField(blank=True, default="")),
                ("risks_related", models.TextField(blank=True, default="")),
                ("complexity", models.CharField(blank=True, default="", max_length=64)),
                ("sop_iop_exists", models.CharField(blank=True, default="", max_length=128)),
                ("training_time_needed", models.CharField(blank=True, default="", max_length=255)),
                ("recommended_handoff_duration", models.CharField(blank=True, default="", max_length=255)),
                ("task_frequency", models.CharField(blank=True, default="", max_length=255)),
                ("unit_of_measure", models.CharField(blank=True, default="", max_length=128)),
                ("volume", models.CharField(blank=True, default="", max_length=64)),
                ("task_time_per_unit", models.CharField(blank=True, default="", max_length=64)),
                ("fte_calculation", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "opportunity_assessment",
                "ordering": ["id"],
                "indexes": [
                    models.Index(
                        fields=["migration_request_id", "l1", "l2", "l3"],
                        name="opportunity_migrati_idx",
                    ),
                ],
            },
        ),
    ]
