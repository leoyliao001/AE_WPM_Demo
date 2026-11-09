from django.urls import path

from api.views.user_name_list import delete_user_names, list_user_names, save_user_names

urlpatterns = [
    path("", list_user_names, name="user-name-list-search"),
    path("data/", save_user_names, name="user-name-list-save"),
    path("data/delete/", delete_user_names, name="user-name-list-delete"),
]