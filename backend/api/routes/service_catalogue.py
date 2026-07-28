from django.urls import path

from api.views.service_catalogue import list_service_catalogue
from api.views.service_catalogue_crud import delete_service_catalogue, save_service_catalogue

urlpatterns = [
    path("", list_service_catalogue, name="service-catalogue-list"),
    path("data/", save_service_catalogue, name="service-catalogue-save"),
    path("data/delete/", delete_service_catalogue, name="service-catalogue-delete"),
]
