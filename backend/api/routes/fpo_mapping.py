from django.urls import path

from api.views.fpo_mapping import list_fpo_mapping

urlpatterns = [
    path("", list_fpo_mapping, name="fpo-mapping-list"),
]
