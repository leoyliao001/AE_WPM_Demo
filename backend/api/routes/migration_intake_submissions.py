from django.urls import path

from api.views.migration_intake_submissions import list_migration_intake_submissions
from api.views.migration_intake_submissions_crud import (
    delete_migration_intake_submissions,
    save_migration_intake_submissions,
)

urlpatterns = [
    path("", list_migration_intake_submissions, name="migration-intake-submissions-list"),
    path("data/", save_migration_intake_submissions, name="migration-intake-submissions-save"),
    path(
        "data/delete/",
        delete_migration_intake_submissions,
        name="migration-intake-submissions-delete",
    ),
]
