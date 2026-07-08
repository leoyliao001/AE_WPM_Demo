from django.urls import path

from api.views.migration_intake import submit_intake

urlpatterns = [
    path("submit/", submit_intake, name="migration-intake-submit"),
]
