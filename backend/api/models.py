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
    business_owner = models.CharField(max_length=255, blank=True, default="")
    target_start_date = models.CharField(max_length=10, blank=True, default="")
    target_end_date = models.CharField(max_length=10, blank=True, default="")
    initial_rationale = models.TextField(blank=True, default="")
    intake_audit_log = models.JSONField(default=list)
    business_case_submission_date = models.DateTimeField(null=True, blank=True)
    business_case_file = models.FileField(
        upload_to="business_case/%Y/%m/", null=True, blank=True, max_length=255
    )
    business_case_file_name = models.CharField(max_length=255, blank=True)
    business_case_file_size = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "migration_intake_submission"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.migration_request_id} — {self.project_name}"


class MigrationIntakeAttachment(models.Model):
    """Attachments for Migration Project Intake Form."""

    submission = models.ForeignKey(
        MigrationIntakeSubmission,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="intake_attachments/%Y/%m/", max_length=255)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=128, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "migration_intake_attachment"
        ordering = ["id"]

    def __str__(self):
        return f"{self.submission.migration_request_id} — {self.file_name}"


class ScopeStatement(models.Model):
    """Per-project scope statement draft and submission record."""

    project = models.OneToOneField(
        MigrationIntakeSubmission,
        on_delete=models.CASCADE,
        related_name="scope_statement",
    )
    scope_text = models.TextField(blank=True, default="")
    out_of_scope = models.TextField(blank=True, default="")
    assumptions = models.TextField(blank=True, default="")
    waves = models.JSONField(default=list)
    review_required = models.BooleanField(default=False)
    status = models.CharField(max_length=16, default="draft")
    revision = models.PositiveIntegerField(default=0)
    ambition_fte = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    final_project_fte = models.PositiveIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.CharField(max_length=254, blank=True, default="")
    audit_log = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scope_statement"

    def __str__(self):
        return f"{self.project.migration_request_id} — Scope Statement"


class ScopeStatementLine(models.Model):
    statement = models.ForeignKey(
        ScopeStatement,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    job_level = models.CharField(
        max_length=3,
        choices=[("JL2", "JL2"), ("JL3", "JL3"), ("JL4", "JL4")],
    )
    agreed_fte = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    not_agreed_fte = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    final_fte = models.PositiveIntegerField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.CharField(max_length=254, blank=True, default="")

    class Meta:
        db_table = "scope_statement_line"
        ordering = ["job_level"]
        constraints = [
            models.UniqueConstraint(fields=["statement", "job_level"], name="scope_unique_job_level"),
        ]

    def __str__(self):
        return f"{self.statement.project.migration_request_id} — {self.job_level}"


class ScopeStatementEvidence(models.Model):
    line = models.ForeignKey(
        ScopeStatementLine,
        on_delete=models.CASCADE,
        related_name="evidence",
    )
    file = models.FileField(upload_to="scope_evidence/%Y/%m/", max_length=255)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    uploaded_by = models.CharField(max_length=254)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scope_statement_evidence"
        ordering = ["id"]


class StakeholderRegistration(models.Model):
    """Per-project manually maintained stakeholder registry for Toll Gates."""

    project = models.OneToOneField(
        MigrationIntakeSubmission,
        on_delete=models.CASCADE,
        related_name="stakeholder_registration",
    )
    team_members = models.JSONField(default=list)
    assignments = models.JSONField(default=dict)
    audit_log = models.JSONField(default=list)
    revision = models.PositiveIntegerField(default=0)
    updated_by = models.CharField(max_length=254, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stakeholder_registration"

    def __str__(self):
        return f"{self.project.migration_request_id} — Stakeholder Registration"


class ProjectCharter(models.Model):
    project = models.OneToOneField(
        MigrationIntakeSubmission, on_delete=models.CASCADE, related_name="project_charter"
    )
    vision = models.TextField(blank=True, default="")
    deliverable_notes = models.JSONField(default=dict)
    extra_success_criteria = models.JSONField(default=list)
    source_fingerprint = models.CharField(max_length=64, blank=True, default="")
    revision = models.PositiveIntegerField(default=0)
    audit_log = models.JSONField(default=list)
    updated_by = models.CharField(max_length=254, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_charter"

    def __str__(self):
        return f"{self.project.migration_request_id} - Project Charter"


class BusinessCase(models.Model):
    project = models.OneToOneField(MigrationIntakeSubmission, on_delete=models.CASCADE, related_name="online_business_case")
    details = models.JSONField(default=dict)
    financial_inputs = models.JSONField(default=dict)
    revision = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=24, default="draft")
    source_fingerprint = models.CharField(max_length=64, blank=True, default="")
    review_required = models.BooleanField(default=False)
    audit_log = models.JSONField(default=list)
    financial_history = models.JSONField(default=list)
    saved_snapshot = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=254, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_case"


class BusinessCaseCostRate(models.Model):
    location = models.CharField(max_length=255)
    job_level = models.CharField(max_length=3, choices=[("JL2", "JL2"), ("JL3", "JL3"), ("JL4", "JL4")])
    annual_cost = models.DecimalField(max_digits=18, decimal_places=4)
    currency = models.CharField(max_length=3, default="USD")
    usd_rate = models.DecimalField(max_digits=18, decimal_places=8, default=1)
    year = models.PositiveSmallIntegerField()
    version = models.CharField(max_length=64)
    audit_log = models.JSONField(default=list)
    updated_by = models.CharField(max_length=254, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_case_cost_rate"
        constraints = [models.UniqueConstraint(fields=["location", "job_level", "year"], name="bc_rate_location_level_year")]


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


class ApprovalInput(models.Model):
    """Activity Function / Product approval stakeholder email mapping."""

    activity_function = models.CharField(max_length=128, blank=True, default="", db_index=True)
    product = models.CharField(max_length=128, blank=True, default="", db_index=True)
    area_head = models.CharField(max_length=255, blank=True, default="", help_text="Area Head email(s).")
    pmo = models.CharField(max_length=255, blank=True, default="", help_text="PMO email(s).")
    bpm = models.CharField(max_length=255, blank=True, default="", help_text="BPM email(s).")
    fbp = models.CharField(max_length=255, blank=True, default="", help_text="FBP email(s).")
    wpm = models.CharField(max_length=255, blank=True, default="", help_text="WPM email(s).")
    elt = models.CharField(max_length=255, blank=True, default="", help_text="ELT email(s).")
    gsc_head = models.CharField(max_length=255, blank=True, default="", help_text="GSC Head email(s).")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "approval_input"
        ordering = ["activity_function", "product"]
        indexes = [
            models.Index(fields=["activity_function", "product"], name="approval_in_act_fun_idx"),
        ]

    def __str__(self):
        return f"{self.activity_function} / {self.product}"


class ProductOwnership(models.Model):
    """Region / Area / Migration Manager ownership mapping."""

    region = models.CharField(max_length=16, blank=True, default="", db_index=True)
    area = models.CharField(max_length=32, blank=True, default="", db_index=True)
    migration_manager = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Email address(es) of the migration manager(s). Comma-separate multiple emails.",
    )
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


class ServiceCatalogue(models.Model):
    """Service catalogue activities (Product / L1–L4 / ownership)."""

    catalogue = models.CharField(max_length=64, blank=True, default="", db_index=True)
    product = models.CharField(max_length=128, blank=True, default="", db_index=True)
    l1 = models.CharField(max_length=128, blank=True, default="", db_index=True)
    l2 = models.CharField(max_length=128, blank=True, default="")
    l3 = models.CharField(max_length=128, blank=True, default="")
    l4 = models.CharField(max_length=255, blank=True, default="")
    current_ownership = models.CharField(max_length=64, blank=True, default="")
    customer = models.CharField(max_length=128, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_catalogue"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["product", "l1", "l2", "l3"]),
            models.Index(fields=["current_ownership"]),
        ]

    def __str__(self):
        return f"{self.product} / {self.l4 or self.l3 or self.id}"


class WorkingHours(models.Model):
    """Area / GSC working hours reference data."""

    area = models.CharField(max_length=64, blank=True, default="", db_index=True)
    aera_working_hours = models.CharField(max_length=32, blank=True, default="")
    gsc = models.CharField(max_length=64, blank=True, default="", db_index=True)
    gsc_working_hours = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "working_hours"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["area", "gsc"], name="working_hou_area_gsc_idx"),
        ]

    def __str__(self):
        return f"{self.area or '-'} / {self.gsc or '-'} / {self.gsc_working_hours}"


class BpmRofo(models.Model):
    """BPM ROFO planning table by onboarding month and year."""

    # Field order below mirrors the "BPM ROFO" sheet column order in Migration Tracking (1).xlsx.
    status = models.CharField(max_length=32, blank=True, default="")
    country = models.CharField(max_length=128, blank=True, default="")
    region = models.CharField(max_length=64, blank=True, default="")
    area = models.CharField(max_length=128, blank=True, default="")
    gsc_site = models.CharField(max_length=64, blank=True, default="")
    function = models.CharField(max_length=128, blank=True, default="")
    function_id_description = models.CharField(max_length=255, blank=True, default="")
    product = models.CharField(max_length=255, blank=True, default="")
    cost_center = models.CharField(max_length=64, blank=True, default="")
    pid = models.CharField(max_length=512, blank=True, default="")
    project_name = models.CharField(max_length=255, blank=True, default="")
    part_not_part_of_rofo = models.CharField(max_length=16, blank=True, default="")
    gsc_leader = models.CharField(max_length=255, blank=True, default="")
    gsc1_leader = models.CharField(max_length=255, blank=True, default="")
    bpm_owner = models.CharField(max_length=255, blank=True, default="")
    bu = models.CharField(max_length=64, blank=True, default="")
    frontline_staff_cost_per_fte = models.CharField(max_length=32, blank=True, default="")
    gsc_staff_cost_per_fte = models.CharField(max_length=32, blank=True, default="")
    project_cost = models.CharField(max_length=32, blank=True, default="")
    x_column = models.CharField(max_length=32, blank=True, default="")
    base_pids = models.CharField(max_length=64, blank=True, default="")
    positions_to_be_offshored_in_gsc = models.CharField(max_length=64, blank=True, default="")
    positions_to_be_released_in_frontline = models.CharField(max_length=64, blank=True, default="")
    rofo_value = models.CharField(max_length=64, blank=True, default="")
    year = models.PositiveSmallIntegerField(default=0)
    onboarding_month = models.CharField(max_length=32, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bpm_rofo"
        ordering = ["-year", "project_name", "id"]
        indexes = [
            models.Index(fields=["year", "onboarding_month"]),
            models.Index(fields=["project_name"]),
        ]

    def __str__(self):
        return f"{self.project_name or 'BPM ROFO'} ({self.year or self.onboarding_month})"


class BpmActual(models.Model):
    """BPM Actuals table by onboarding month and year."""

    # Field order below mirrors the "BPM Actual" sheet column order in Migration Tracking (1).xlsx.
    status = models.CharField(max_length=32, blank=True, default="")
    country = models.CharField(max_length=128, blank=True, default="")
    region = models.CharField(max_length=64, blank=True, default="")
    area = models.CharField(max_length=128, blank=True, default="")
    gsc_site = models.CharField(max_length=64, blank=True, default="")
    function = models.CharField(max_length=128, blank=True, default="")
    function_id_description = models.CharField(max_length=255, blank=True, default="")
    product = models.CharField(max_length=255, blank=True, default="")
    cost_center = models.CharField(max_length=64, blank=True, default="")
    pid = models.CharField(max_length=512, blank=True, default="")
    project_name = models.CharField(max_length=255, blank=True, default="")
    part_not_part_of_rofo = models.CharField(max_length=16, blank=True, default="")
    gsc_leader = models.CharField(max_length=255, blank=True, default="")
    gsc1_leader = models.CharField(max_length=255, blank=True, default="")
    bpm_owner = models.CharField(max_length=255, blank=True, default="")
    bu = models.CharField(max_length=64, blank=True, default="")
    frontline_staff_cost_per_fte = models.CharField(max_length=32, blank=True, default="")
    gsc_staff_cost_per_fte = models.CharField(max_length=32, blank=True, default="")
    project_cost = models.CharField(max_length=32, blank=True, default="")
    x_column = models.CharField(max_length=32, blank=True, default="")
    base_pids = models.CharField(max_length=64, blank=True, default="")
    positions_to_be_offshored_in_gsc = models.CharField(max_length=64, blank=True, default="")
    positions_to_be_released_in_frontline = models.CharField(max_length=64, blank=True, default="")
    actual_value = models.CharField(max_length=64, blank=True, default="")
    year = models.PositiveSmallIntegerField(default=0)
    onboarding_month = models.CharField(max_length=32, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bpm_actual"
        ordering = ["-year", "project_name", "id"]
        indexes = [
            models.Index(fields=["year", "onboarding_month"]),
            models.Index(fields=["project_name"]),
        ]

    def __str__(self):
        return f"{self.project_name or 'BPM Actual'} ({self.year or self.onboarding_month})"


class ExecutiveSummaryNote(models.Model):
    """Editable notes displayed in the Executive Summary side panels."""

    section = models.CharField(max_length=32, blank=True, default="")
    year = models.PositiveSmallIntegerField(default=0)
    title = models.CharField(max_length=64, blank=True, default="")
    body = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "executive_summary_note"
        ordering = ["year", "section", "id"]
        indexes = [
            models.Index(fields=["year", "section"], name="exec_summary_year_section_idx"),
        ]

    def __str__(self):
        return f"{self.section or 'summary'} ({self.year})"


class ProjectAttributesAccess(models.Model):
    """SSO email-based access control for Project Attributes Database tables."""

    email = models.CharField(max_length=255, unique=True, db_index=True)
    is_super_admin = models.BooleanField(default=False)
    fpo_mapping = models.BooleanField(default=False)
    product_ownership = models.BooleanField(default=False)
    gsc_site_mapping = models.BooleanField(default=False)
    service_catalogue = models.BooleanField(default=False)
    working_hours = models.BooleanField(default=False)
    project_gantt = models.BooleanField(default=False)
    migration_intake = models.BooleanField(default=False)
    approval_workflow = models.BooleanField(default=False)
    input_for_approval = models.BooleanField(default=False)
    bpm_rofo = models.BooleanField(default=False)
    bpm_actual = models.BooleanField(default=False)
    access_control = models.BooleanField(default=False)
    scope_statement = models.BooleanField(default=False)
    stakeholder_registration = models.BooleanField(default=False)
    project_charter = models.BooleanField(default=False)
    business_case = models.BooleanField(default=False)
    cost_rates = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_attributes_access"
        ordering = ["email"]

    def __str__(self):
        role = "super_admin" if self.is_super_admin else "user"
        return f"{self.email} ({role})"


class ApprovalWorkflow(models.Model):
    """Approval Workflow statuses — synced automatically; UI is read-only."""

    migration_request_id = models.CharField(max_length=32, unique=True, db_index=True)
    business_case_submitted_date = models.DateTimeField(null=True, blank=True)
    area_head_approval_trigger_date = models.DateTimeField(null=True, blank=True)
    area_head_comments = models.TextField(blank=True, default="")
    area_head_final_date = models.DateTimeField(null=True, blank=True)
    area_head_status = models.CharField(max_length=64, blank=True, default="")
    area_head_approved_by = models.CharField(max_length=255, blank=True, default="")
    pmo_review_comment = models.TextField(blank=True, default="")
    pmo_review_date = models.DateTimeField(null=True, blank=True)
    pmo_status = models.CharField(max_length=64, blank=True, default="")
    pmo_approved_by = models.CharField(max_length=255, blank=True, default="")
    bpm_budget_status = models.CharField(max_length=64, blank=True, default="")
    bpm_status = models.CharField(max_length=64, blank=True, default="")
    bpm_comment = models.TextField(blank=True, default="")
    bpm_review_date = models.DateTimeField(null=True, blank=True)
    bpm_approved_by = models.CharField(max_length=255, blank=True, default="")
    fbp_review_date = models.DateTimeField(null=True, blank=True)
    fbp_comment = models.TextField(blank=True, default="")
    fbp_status = models.CharField(max_length=64, blank=True, default="")
    fbp_approved_by = models.CharField(max_length=255, blank=True, default="")
    wpm_review_date = models.DateTimeField(null=True, blank=True)
    wpm_review_comment = models.TextField(blank=True, default="")
    wpm_review_status = models.CharField(max_length=64, blank=True, default="")
    wpm_approved_by = models.CharField(max_length=255, blank=True, default="")
    gsc_head_date = models.DateTimeField(null=True, blank=True)
    gsc_head_comment = models.TextField(blank=True, default="")
    gsc_head_status = models.CharField(max_length=64, blank=True, default="")
    gsc_head_approved_by = models.CharField(max_length=255, blank=True, default="")
    elt_date = models.DateTimeField(null=True, blank=True)
    elt_comment = models.TextField(blank=True, default="")
    elt_status = models.CharField(max_length=64, blank=True, default="")
    elt_approved_by = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "approval_workflow"
        ordering = ["-updated_at", "id"]

    def __str__(self):
        return f"Approval Workflow — {self.migration_request_id}"


class ProjectGanttPlan(models.Model):
    """Per-project Gantt task week spans (editable bars)."""

    project = models.OneToOneField(
        MigrationIntakeSubmission,
        on_delete=models.CASCADE,
        related_name="gantt_plan",
    )
    migration_request_id = models.CharField(
        max_length=32,
        blank=True,
        default="",
        db_index=True,
        help_text="Denormalized Migration Request ID (e.g. WPM_PRJ_...) for easier lookup.",
    )
    tasks = models.JSONField(
        default=list,
        help_text=(
            "[{id, name, plan:{startWeek,endWeek}, actual, completedAt, "
            "comments:[{id, at, text, updatedBy, fromPlan, toPlan}]}, ...]"
        ),
    )
    meta = models.JSONField(
        default=dict,
        blank=True,
        help_text="Project summary fields (phase, scope, FTE, HC, totals).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_gantt_plan"

    def __str__(self):
        mid = self.migration_request_id or self.project_id
        return f"Gantt plan for {mid}"
