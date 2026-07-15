from django.urls import path

from api.views.fpo_mapping import list_fpo_mapping
from api.views.fpo_mapping_crud import delete_fpo_mapping, save_fpo_mapping

urlpatterns = [
    path("", list_fpo_mapping, name="fpo-mapping-list"),
    path("data/", save_fpo_mapping, name="fpo-mapping-save"),
    path("data/delete/", delete_fpo_mapping, name="fpo-mapping-delete"),
]
