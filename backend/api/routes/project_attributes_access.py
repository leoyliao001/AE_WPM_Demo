from django.urls import path

from api.views.project_attributes_access import list_project_attributes_access, my_attributes_access
from api.views.project_attributes_access_crud import (
    delete_project_attributes_access,
    save_project_attributes_access,
)

urlpatterns = [
    path("me/", my_attributes_access, name="project-attributes-access-me"),
    path("", list_project_attributes_access, name="project-attributes-access-list"),
    path("data/", save_project_attributes_access, name="project-attributes-access-save"),
    path(
        "data/delete/",
        delete_project_attributes_access,
        name="project-attributes-access-delete",
    ),
]
