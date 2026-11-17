from django.urls import path

from api.views.migration_team import delete_migration_team, list_migration_team, save_migration_team

urlpatterns = [
    path("", list_migration_team, name="migration-team-list"),
    path("data/", save_migration_team, name="migration-team-save"),
    path("data/delete/", delete_migration_team, name="migration-team-delete"),
]
