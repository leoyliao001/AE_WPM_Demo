from django.urls import path

from api.views.project_gantt_attributes import (
    get_project_gantt_attributes,
    save_project_gantt_attributes,
)

urlpatterns = [
    path("", get_project_gantt_attributes, name="project-gantt-attributes-get"),
    path("data/", save_project_gantt_attributes, name="project-gantt-attributes-save"),
]
