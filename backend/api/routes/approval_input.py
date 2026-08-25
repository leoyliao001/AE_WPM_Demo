from django.urls import path

from api.views.approval_input import list_approval_input
from api.views.approval_input_crud import delete_approval_input, save_approval_input

urlpatterns = [
    path("", list_approval_input, name="approval-input-list"),
    path("data/", save_approval_input, name="approval-input-save"),
    path("data/delete/", delete_approval_input, name="approval-input-delete"),
]
