from django.urls import path

from api.views.working_hours import list_working_hours
from api.views.working_hours_crud import delete_working_hours, save_working_hours

urlpatterns = [
    path("", list_working_hours, name="working-hours-list"),
    path("data/", save_working_hours, name="working-hours-save"),
    path("data/delete/", delete_working_hours, name="working-hours-delete"),
]
