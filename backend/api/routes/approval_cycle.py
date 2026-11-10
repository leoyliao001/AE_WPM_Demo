from django.urls import path

from api.views.approval_cycle import list_approval_queue, submit_approval_decision
from api.views.fpo_catalogue_requests import decide_fpo_catalogue_request

urlpatterns = [
    path("queue/", list_approval_queue, name="approval-cycle-queue"),
    path("decision/", submit_approval_decision, name="approval-cycle-decision"),
    path("fpo-requests/<int:request_id>/decision/", decide_fpo_catalogue_request, name="fpo-catalogue-request-decision"),
]
