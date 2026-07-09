from django.contrib import admin

from api.models import MigrationIntakeSubmission


@admin.register(MigrationIntakeSubmission)
class MigrationIntakeSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "migration_request_id",
        "project_name",
        "requestor",
        "region",
        "status",
        "created_at",
    )
    list_filter = ("status", "region", "supporting_gsc_sites_custom", "created_at")
    search_fields = (
        "migration_request_id",
        "project_name",
        "requestor",
        "function_name",
    )
    readonly_fields = ("created_at", "updated_at")
