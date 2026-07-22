from django.urls import path

from api.views.gsc_site_mapping import list_gsc_site_mapping
from api.views.gsc_site_mapping_crud import delete_gsc_site_mapping, save_gsc_site_mapping

urlpatterns = [
    path("", list_gsc_site_mapping, name="gsc-site-mapping-list"),
    path("data/", save_gsc_site_mapping, name="gsc-site-mapping-save"),
    path("data/delete/", delete_gsc_site_mapping, name="gsc-site-mapping-delete"),
]
