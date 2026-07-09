from django.urls import path

from api.views.migration_dashboard import list_projects, project_detail

urlpatterns = [
    path("projects/", list_projects, name="migration-dashboard-projects"),
    path("projects/<int:project_id>/", project_detail, name="migration-dashboard-project-detail"),
]
