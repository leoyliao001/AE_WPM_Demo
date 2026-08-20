from django.urls import path

from api.views.approval_workflow import list_approval_workflow

urlpatterns = [
    path("", list_approval_workflow, name="approval-workflow-list"),
]
