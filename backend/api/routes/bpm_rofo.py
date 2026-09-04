from django.urls import path

from api.views.bpm_rofo import list_bpm_rofo
from api.views.bpm_rofo_crud import delete_bpm_rofo, save_bpm_rofo

urlpatterns = [
    path("", list_bpm_rofo, name="bpm-rofo-list"),
    path("data/", save_bpm_rofo, name="bpm-rofo-save"),
    path("data/delete/", delete_bpm_rofo, name="bpm-rofo-delete"),
]
