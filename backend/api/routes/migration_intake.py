from django.urls import path

from api.views.migration_intake import download_attachment, submit_intake

urlpatterns = [
    path("submit/", submit_intake, name="migration-intake-submit"),
    path("attachments/<int:attachment_id>/download/", download_attachment, name="migration-intake-attachment-download"),
]
