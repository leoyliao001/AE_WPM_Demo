from django.db import models


class MigrationIntakeSubmission(models.Model):
    """Migration Project Intake Form — single-table storage."""

    migration_request_id = models.CharField(max_length=32, unique=True, db_index=True)
    requested_date = models.CharField(max_length=64)
    requestor = models.CharField(max_length=128)
    status = models.CharField(max_length=32, default="new")

    project_name = models.CharField(max_length=255)
    migration_type = models.CharField(max_length=128)
    migration_type_value = models.CharField(max_length=64)
    region = models.CharField(max_length=16)

    areas = models.JSONField(default=list)
    countries = models.JSONField(default=list)
    location_strategies = models.JSONField(default=list)
    area_location_pairs = models.JSONField(default=list)
    area_country_pairs = models.JSONField(default=list)

    default_supporting_gsc_sites = models.JSONField(default=list)
    custom_supporting_gsc_sites = models.JSONField(default=list)
    supporting_gsc_sites_custom = models.BooleanField(default=False)
    custom_supporting_justification = models.TextField(blank=True)
    custom_approval_file_name = models.CharField(max_length=255, blank=True)
    custom_approval_file_size = models.PositiveIntegerField(null=True, blank=True)
    custom_approval_file_type = models.CharField(max_length=128, blank=True)

    function_name = models.CharField(max_length=255)
    products = models.JSONField(default=list)
    proposed_scope = models.TextField()
    language_dependencies = models.JSONField(default=list)

    fte_number = models.CharField(max_length=8)
    jl2 = models.CharField(max_length=8, default="0")
    jl3 = models.CharField(max_length=8, default="0")
    jl4 = models.CharField(max_length=8, default="0")
    job_level_total = models.PositiveSmallIntegerField(default=0)
    risks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "migration_intake_submission"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.migration_request_id} — {self.project_name}"
