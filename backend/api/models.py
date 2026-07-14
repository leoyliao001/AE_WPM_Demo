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
    area_country_pairs = models.JSONField(default=list)

    default_location_strategies = models.JSONField(default=list)
    custom_location_strategies = models.JSONField(default=list)
    location_strategy_custom = models.BooleanField(default=False)
    custom_location_strategy_justification = models.TextField(blank=True)
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


class FpoMapping(models.Model):
    """FPO extended list — hierarchical process / FPO mapping."""

    l1 = models.CharField(max_length=128, blank=True, default="")
    gpl = models.CharField(max_length=64, blank=True, default="")
    l2 = models.CharField(max_length=128, blank=True, default="")
    sfpo = models.CharField(max_length=128, blank=True, default="")
    num_business_policy = models.CharField(max_length=16, blank=True, default="")
    l3 = models.CharField(max_length=128, blank=True, default="")
    fpo = models.CharField(max_length=255, blank=True, default="")
    risk_link = models.TextField(blank=True, default="")
    control_link = models.TextField(blank=True, default="")
    l4 = models.CharField(max_length=255, blank=True, default="")
    activity_type = models.CharField(max_length=64, blank=True, default="")
    sub_process_call_activity = models.CharField(max_length=255, blank=True, default="")
    activity_type_2 = models.CharField(max_length=64, blank=True, default="")
    assigned_models_from_l5 = models.CharField(max_length=255, blank=True, default="")
    process_level = models.CharField(max_length=16, blank=True, default="")
    process_grouping = models.CharField(max_length=32, blank=True, default="")
    last_change = models.CharField(max_length=64, blank=True, default="")
    guid = models.CharField(max_length=64, blank=True, default="", db_index=True)
    connect_link = models.TextField(blank=True, default="")
    num_automated_activities = models.CharField(max_length=16, blank=True, default="")
    num_system_supported_activities = models.CharField(max_length=16, blank=True, default="")
    num_manual_activities = models.CharField(max_length=16, blank=True, default="")
    num_undefined_activities = models.CharField(max_length=16, blank=True, default="")
    num_sub_process_activities = models.CharField(max_length=16, blank=True, default="")
    num_ms_office_activities = models.CharField(max_length=16, blank=True, default="")
    num_touchpoint_external_parties = models.CharField(max_length=16, blank=True, default="")
    num_risks = models.CharField(max_length=16, blank=True, default="")
    num_controls = models.CharField(max_length=16, blank=True, default="")
    num_manual_controls = models.CharField(max_length=16, blank=True, default="")
    num_business_rules = models.CharField(max_length=16, blank=True, default="")
    report_generation_date = models.CharField(max_length=32, blank=True, default="")
    sharepoint_link_sop = models.TextField(blank=True, default="")

    class Meta:
        db_table = "fpo_mapping"
        indexes = [
            models.Index(fields=["l1", "l2", "l3"]),
            models.Index(fields=["fpo"]),
            models.Index(fields=["sfpo"]),
        ]

    def __str__(self):
        return f"{self.l1} / {self.l2} / {self.l3} / {self.fpo}"
