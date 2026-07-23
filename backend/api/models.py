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
    is_reference = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True = Excel dictionary row for cascade dropdowns only; not shown in the grid.",
    )

    class Meta:
        db_table = "fpo_mapping"
        indexes = [
            models.Index(fields=["l1", "l2", "l3"]),
            models.Index(fields=["fpo"]),
            models.Index(fields=["sfpo"]),
        ]

    def __str__(self):
        return f"{self.l1} / {self.l2} / {self.l3} / {self.fpo}"


class OpportunityAssessment(models.Model):
    """Task-level Opportunity Assessment scoped to a migration request."""

    migration_request_id = models.CharField(max_length=32, db_index=True)
    product = models.CharField(max_length=128, blank=True, default="")
    owner = models.CharField(max_length=128, blank=True, default="")
    location = models.CharField(max_length=128, blank=True, default="")
    l1 = models.CharField(max_length=128, blank=True, default="")
    l2 = models.CharField(max_length=128, blank=True, default="")
    l3 = models.CharField(max_length=128, blank=True, default="")
    l4 = models.CharField(max_length=255, blank=True, default="")
    task_name = models.CharField(max_length=255, blank=True, default="")
    task_description = models.TextField(blank=True, default="")
    upstream = models.TextField(blank=True, default="")
    downstream = models.TextField(blank=True, default="")
    risks_related = models.TextField(blank=True, default="")
    complexity = models.CharField(max_length=64, blank=True, default="")
    sop_iop_exists = models.CharField(max_length=128, blank=True, default="")
    training_time_needed = models.CharField(max_length=255, blank=True, default="")
    recommended_handoff_duration = models.CharField(max_length=255, blank=True, default="")
    task_frequency = models.CharField(max_length=255, blank=True, default="")
    unit_of_measure = models.CharField(max_length=128, blank=True, default="")
    volume_monthly = models.CharField(max_length=64, blank=True, default="")
    task_time_per_unit_min = models.CharField(max_length=64, blank=True, default="")
    area = models.CharField(max_length=64, blank=True, default="")
    gsc_site = models.CharField(max_length=128, blank=True, default="")
    task_found_in_service_catalog = models.CharField(max_length=255, blank=True, default="")
    migratable_to_gsc = models.CharField(max_length=255, blank=True, default="")
    fte_calculation = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "opportunity_assessment"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["migration_request_id", "l1", "l2", "l3"]),
        ]
    
    def __str__(self):
        return f"{self.migration_request_id} — {self.task_name or self.l4 or self.id}"


class ProductOwnership(models.Model):
    """Region / Area / Migration Manager ownership mapping."""

    region = models.CharField(max_length=16, blank=True, default="", db_index=True)
    area = models.CharField(max_length=32, blank=True, default="", db_index=True)
    migration_manager = models.CharField(max_length=128, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_ownership"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["region", "area"]),
            models.Index(fields=["migration_manager"]),
        ]

    def __str__(self):
        return f"{self.region} / {self.area} / {self.migration_manager}"


class GscSiteMapping(models.Model):
    """Region / Area / Supporting GSC Sites mapping (Sheet2)."""

    region = models.CharField(max_length=16, blank=True, default="", db_index=True)
    area = models.CharField(max_length=32, blank=True, default="", db_index=True)
    supporting_gsc_sites = models.CharField(max_length=255, blank=True, default="")
    all_options = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gsc_site_mapping"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["region", "area"]),
        ]

    def __str__(self):
        return f"{self.region} / {self.area} / {self.supporting_gsc_sites}"


class ProjectAttributesAccess(models.Model):
    """SSO email-based access control for Project Attributes Database tables."""

    email = models.CharField(max_length=255, unique=True, db_index=True)
    is_super_admin = models.BooleanField(default=False)
    fpo_mapping = models.BooleanField(default=False)
    product_ownership = models.BooleanField(default=False)
    gsc_site_mapping = models.BooleanField(default=False)
    access_control = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_attributes_access"
        ordering = ["email"]

    def __str__(self):
        role = "super_admin" if self.is_super_admin else "user"
        return f"{self.email} ({role})"

