from django.urls import path

from api.views.bpm_actual import list_bpm_actual
from api.views.bpm_actual_crud import delete_bpm_actual, save_bpm_actual

urlpatterns = [
    path("", list_bpm_actual, name="bpm-actual-list"),
    path("data/", save_bpm_actual, name="bpm-actual-save"),
    path("data/delete/", delete_bpm_actual, name="bpm-actual-delete"),
]
