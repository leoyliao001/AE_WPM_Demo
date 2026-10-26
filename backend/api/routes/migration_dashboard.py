from django.urls import path

from api.views.migration_dashboard import (
    download_business_case,
    list_projects,
    project_detail,
    submit_business_case,
)
from api.views.project_gantt import project_gantt
from api.views.opportunity_assessment import (
    delete_opportunity_assessment,
    download_opportunity_template,
    list_opportunity_assessment,
    save_opportunity_assessment,
    upload_opportunity_excel,
)
from api.views.scope_statement import (
    download_scope_evidence,
    delete_scope_statement_database,
    get_scope_statement,
    list_scope_statement_database,
    save_scope_statement_database,
    save_scope_statement,
    upload_scope_evidence,
)

urlpatterns = [
    path("projects/", list_projects, name="migration-dashboard-projects"),
    path("scope-statements/", list_scope_statement_database, name="scope-statement-database"),
    path("scope-statements/data/", save_scope_statement_database, name="scope-statement-database-save"),
    path("scope-statements/data/delete/", delete_scope_statement_database, name="scope-statement-database-delete"),
    path("projects/<int:project_id>/scope-statement/", get_scope_statement, name="scope-statement"),
    path("projects/<int:project_id>/scope-statement/save/", save_scope_statement, name="scope-statement-save"),
    path(
        "projects/<int:project_id>/scope-statement/evidence/<str:job_level>/",
        upload_scope_evidence,
        name="scope-statement-evidence",
    ),
    path(
        "projects/<int:project_id>/scope-statement/evidence/download/<int:evidence_id>/",
        download_scope_evidence,
        name="scope-statement-evidence-download",
    ),
    path("projects/<int:project_id>/", project_detail, name="migration-dashboard-project-detail"),
    path(
        "projects/<int:project_id>/business-case/submit/",
        submit_business_case,
        name="migration-dashboard-business-case-submit",
    ),
    path(
        "projects/<int:project_id>/business-case/file/",
        download_business_case,
        name="migration-dashboard-business-case-file",
    ),
    path(
        "projects/<int:project_id>/gantt/",
        project_gantt,
        name="project-gantt",
    ),
    path(
        "projects/<int:project_id>/opportunity-assessment/",
        list_opportunity_assessment,
        name="opportunity-assessment-list",
    ),
    path(
        "projects/<int:project_id>/opportunity-assessment/data/",
        save_opportunity_assessment,
        name="opportunity-assessment-save",
    ),
    path(
        "projects/<int:project_id>/opportunity-assessment/data/delete/",
        delete_opportunity_assessment,
        name="opportunity-assessment-delete",
    ),
    path(
        "projects/<int:project_id>/opportunity-assessment/template/",
        download_opportunity_template,
        name="opportunity-assessment-template",
    ),
    path(
        "projects/<int:project_id>/opportunity-assessment/upload/",
        upload_opportunity_excel,
        name="opportunity-assessment-upload",
    ),
]
