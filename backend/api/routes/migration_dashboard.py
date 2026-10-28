from django.urls import path
from api.views.business_case import (
    get_business_case, save_business_case, list_business_cases, delete_business_case,
    cost_rates, delete_cost_rate,
)

from api.views.migration_dashboard import (
    download_business_case,
    list_projects,
    project_detail,
    submit_business_case,
)
from api.views.project_gantt import project_gantt
from api.views.project_charter import (
    get_project_charter,
    save_project_charter,
    list_project_charters,
    delete_project_charter,
)
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
from api.views.stakeholder_registration import list_stakeholder_registrations
from api.views.stakeholder_registration import (
    get_stakeholder_registration,
    save_stakeholder_registration,
)

urlpatterns = [
    path("business-cases/", list_business_cases, name="business-case-database"),
    path("cost-rates/", cost_rates, name="business-case-cost-rates"),
    path("cost-rates/<int:rate_id>/", delete_cost_rate, name="business-case-cost-rate-delete"),
    path("projects/<int:project_id>/business-case/", get_business_case, name="online-business-case"),
    path("projects/<int:project_id>/business-case/save/", save_business_case, name="online-business-case-save"),
    path("projects/<int:project_id>/business-case/delete/", delete_business_case, name="online-business-case-delete"),
    path("project-charters/", list_project_charters, name="project-charter-database"),
    path("projects/<int:project_id>/project-charter/", get_project_charter, name="project-charter"),
    path("projects/<int:project_id>/project-charter/save/", save_project_charter, name="project-charter-save"),
    path("projects/<int:project_id>/project-charter/delete/", delete_project_charter, name="project-charter-delete"),
    path("projects/", list_projects, name="migration-dashboard-projects"),
    path("stakeholder-registrations/", list_stakeholder_registrations, name="stakeholder-registration-database"),
    path(
        "projects/<int:project_id>/stakeholder-registration/",
        get_stakeholder_registration,
        name="stakeholder-registration",
    ),
    path(
        "projects/<int:project_id>/stakeholder-registration/save/",
        save_stakeholder_registration,
        name="stakeholder-registration-save",
    ),
    path("scope-statements/", list_scope_statement_database, name="scope-statement-database"),
    path("scope-statements/data/", save_scope_statement_database, name="scope-statement-database-save"),
    path("scope-statements/data/delete/", delete_scope_statement_database, name="scope-statement-database-delete"),
    path("projects/<int:project_id>/scope-statement/", get_scope_statement, name="scope-statement"),
    path("projects/<int:project_id>/scope-statement/save/", save_scope_statement, name="scope-statement-save"),
    path("projects/<int:project_id>/scope-statement/attachments/", upload_scope_evidence, name="scope-statement-attachments"),
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
