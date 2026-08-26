from django.urls import path

from api.views.approval_cycle import list_approval_queue, submit_approval_decision

urlpatterns = [
    path("queue/", list_approval_queue, name="approval-cycle-queue"),
    path("decision/", submit_approval_decision, name="approval-cycle-decision"),
]
