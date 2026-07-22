from django.urls import path

from api.views.product_ownership import list_product_ownership
from api.views.product_ownership_crud import delete_product_ownership, save_product_ownership

urlpatterns = [
    path("", list_product_ownership, name="product-ownership-list"),
    path("data/", save_product_ownership, name="product-ownership-save"),
    path("data/delete/", delete_product_ownership, name="product-ownership-delete"),
]
