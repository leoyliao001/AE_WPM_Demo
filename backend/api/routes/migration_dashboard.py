from django.urls import path

from api.views.migration_dashboard import list_projects, project_detail
from api.views.opportunity_assessment import (
    delete_opportunity_assessment,
    download_opportunity_template,
    list_opportunity_assessment,
    save_opportunity_assessment,
    upload_opportunity_excel,
)

urlpatterns = [
    path("projects/", list_projects, name="migration-dashboard-projects"),
    path("projects/<int:project_id>/", project_detail, name="migration-dashboard-project-detail"),
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
