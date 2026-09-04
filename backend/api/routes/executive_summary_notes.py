from django.urls import path

from api.views.executive_summary_notes import list_executive_summary_notes, save_executive_summary_notes

urlpatterns = [
    path("", list_executive_summary_notes, name="executive-summary-notes-list"),
    path("data/", save_executive_summary_notes, name="executive-summary-notes-save"),
]
