from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from api.models import (
    FpoCatalogueRequest,
    MigrationIntakeSubmission,
    ServiceCatalogue,
    StakeholderRegistration,
)


class FpoCatalogueReminderTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="FPO-REMINDER-TEST",
            requested_date="2026-11-10",
            requestor="owner@example.com",
            project_name="FPO reminder test",
            migration_type="Other",
            migration_type_value="other",
            region="APA",
            areas=["SEA"],
            countries=["Singapore"],
            function_name="Operations",
            products=["LCL"],
            proposed_scope="Test scope",
            fte_number="1",
        )
        StakeholderRegistration.objects.create(
            project=self.project,
            team_members=[
                {
                    "id": "assigned-fpo",
                    "fullName": "Assigned FPO",
                    "email": "fpo@example.com",
                }
            ],
            assignments={"fpo": {"personIds": ["assigned-fpo"]}},
        )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.scope_url = f"/api/migration-dashboard/projects/{self.project.pk}/opportunity-assessment/task-scope/"
        self.request_url = f"/api/migration-dashboard/projects/{self.project.pk}/opportunity-assessment/catalogue-requests/"
        self.payload = {
            "product": "LCL",
            "l1": "New L1",
            "l2": "New L2",
            "l3": "New L3",
            "l4": "New L4",
            "request_comment": "This process is not present in the current catalogue.",
        }

    def test_reminder_persists_until_approved_hierarchy_is_acknowledged(self):
        from unittest.mock import patch

        with self.settings(FPO_CATALOGUE_APPROVER_EMAIL="someone-else@example.com"):
            with patch("api.views.fpo_catalogue_requests._send_request_email"):
                response = self.client.post(self.request_url, self.payload, format="json")

        self.assertEqual(response.status_code, 201, response.data)
        request = FpoCatalogueRequest.objects.get(pk=response.data["id"])
        self.assertEqual(request.approver_email, "fpo@example.com")
        self.assertEqual(response.data["approver"], "fpo@example.com")
        self.assertEqual(request.request_comment, self.payload["request_comment"])
        reminder = self.client.get(self.scope_url).data["catalogue_requests"][0]
        self.assertEqual(reminder["status"], "pending")
        self.assertEqual(reminder["l4"], "New L4")

        request.status = "approved"
        request.save(update_fields=["status"])
        approved_reminder = self.client.get(self.scope_url).data["catalogue_requests"][0]
        self.assertEqual(approved_reminder["status"], "approved")

        acknowledge_url = f"{self.request_url}{request.pk}/acknowledge/"
        mismatch = {**self.payload, "l4": "Different L4"}
        self.assertEqual(self.client.post(acknowledge_url, mismatch, format="json").status_code, 400)
        self.assertEqual(self.client.get(self.scope_url).data["catalogue_requests"][0]["status"], "approved")

        acknowledged = self.client.post(acknowledge_url, self.payload, format="json")
        self.assertEqual(acknowledged.status_code, 200, acknowledged.data)
        self.assertIsNotNone(request.__class__.objects.get(pk=request.pk).catalogue_updated_at)
        self.assertEqual(self.client.get(self.scope_url).data["catalogue_requests"], [])

    def test_request_requires_exactly_one_assigned_project_fpo(self):
        registration = StakeholderRegistration.objects.get(project=self.project)
        registration.assignments = {"fpo": {"personIds": []}}
        registration.save(update_fields=["assignments"])

        response = self.client.post(self.request_url, self.payload, format="json")

        self.assertEqual(response.status_code, 409)
        self.assertIn("exactly one FPO", response.data["error"])
        self.assertEqual(FpoCatalogueRequest.objects.count(), 0)

    def test_pending_request_cannot_be_acknowledged(self):
        request = FpoCatalogueRequest.objects.create(
            project=self.project,
            requested_by="owner@example.com",
            approver_email="fpo@example.com",
            **self.payload,
        )
        url = f"{self.request_url}{request.pk}/acknowledge/"
        response = self.client.post(url, self.payload, format="json")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.get(self.scope_url).data["catalogue_requests"][0]["status"], "pending")

    def test_oa_loads_before_fpo_migration_is_applied(self):
        from unittest.mock import patch

        with patch("api.views.fpo_catalogue_requests._request_table_available", return_value=False):
            scope_response = self.client.get(self.scope_url)
            submit_response = self.client.post(self.request_url, self.payload, format="json")

        self.assertEqual(scope_response.status_code, 200, scope_response.data)
        self.assertEqual(scope_response.data["catalogue_requests"], [])
        self.assertEqual(submit_response.status_code, 503, submit_response.data)
        self.assertIn("migration", submit_response.data["error"].lower())

    def test_request_reason_is_required(self):
        payload = {key: value for key, value in self.payload.items() if key != "request_comment"}
        response = self.client.post(self.request_url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("reason", response.data["error"].lower())

    def test_approval_inserts_and_exposes_catalogue_entry(self):
        request = FpoCatalogueRequest.objects.create(
            project=self.project,
            requested_by="owner@example.com",
            approver_email="fpo@example.com",
            **self.payload,
        )
        self.client.credentials(HTTP_X_USER_EMAIL="fpo@example.com")
        from unittest.mock import Mock, patch

        with patch("api.views.fpo_catalogue_requests.requests.post", return_value=Mock(status_code=202)) as send:
            response = self.client.post(
                f"/api/approval-cycle/fpo-requests/{request.pk}/decision/",
                {"action": "approved", "comment": "Approved"},
                format="json",
            )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["notification_sent"])
        self.assertEqual(send.call_args.kwargs["json"]["personalizations"][0]["to"], [{"email": "owner@example.com"}])
        self.assertTrue(ServiceCatalogue.objects.filter(
            product="LCL", l1="New L1", l2="New L2", l3="New L3", l4="New L4"
        ).exists())

        from api.views.opportunity_task_scope import _catalogue, _catalogue_additions

        _catalogue.cache_clear()
        _catalogue_additions.cache_clear()
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        additions = self.client.get(self.scope_url).data["catalogue_additions"]
        self.assertIn(["LCL", "New L1", "New L2", "New L3", "New L4", "", "", "", "New L4"], additions)

    def test_rejection_notifies_requester_without_catalogue_insert(self):
        request = FpoCatalogueRequest.objects.create(
            project=self.project,
            requested_by="owner@example.com",
            approver_email="fpo@example.com",
            **self.payload,
        )
        self.client.credentials(HTTP_X_USER_EMAIL="fpo@example.com")
        from unittest.mock import Mock, patch

        with patch("api.views.fpo_catalogue_requests.requests.post", return_value=Mock(status_code=202)) as send:
            response = self.client.post(
                f"/api/approval-cycle/fpo-requests/{request.pk}/decision/",
                {"action": "rejected", "comment": "Please clarify scope."},
                format="json",
            )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["notification_sent"])
        self.assertEqual(FpoCatalogueRequest.objects.get(pk=request.pk).status, "rejected")
        self.assertFalse(ServiceCatalogue.objects.filter(
            product="LCL", l1="New L1", l2="New L2", l3="New L3", l4="New L4"
        ).exists())
        email = send.call_args.kwargs["json"]
        self.assertEqual(email["personalizations"][0]["to"], [{"email": "owner@example.com"}])
        self.assertIn("rejected", email["content"][0]["value"])
        self.assertIn("Please clarify scope.", email["content"][0]["value"])

    def test_decision_is_saved_when_applicant_notification_fails(self):
        request = FpoCatalogueRequest.objects.create(
            project=self.project,
            requested_by="owner@example.com",
            approver_email="fpo@example.com",
            **self.payload,
        )
        self.client.credentials(HTTP_X_USER_EMAIL="fpo@example.com")
        from unittest.mock import patch

        with patch("api.views.fpo_catalogue_requests.requests.post", side_effect=TimeoutError("network unavailable")):
            response = self.client.post(
                f"/api/approval-cycle/fpo-requests/{request.pk}/decision/",
                {"action": "approved", "comment": "Approved"},
                format="json",
            )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data["notification_sent"])
        self.assertEqual(FpoCatalogueRequest.objects.get(pk=request.pk).status, "approved")
        self.assertTrue(ServiceCatalogue.objects.filter(
            product="LCL", l1="New L1", l2="New L2", l3="New L3", l4="New L4"
        ).exists())

    @override_settings(SENDGRID_API_KEY="test-key", DEFAULT_FROM_EMAIL="noreply@example.com")
    def test_fpo_email_uses_configured_sendgrid_api(self):
        request = FpoCatalogueRequest.objects.create(
            project=self.project,
            requested_by="owner@example.com",
            approver_email="fpo@example.com",
            **self.payload,
        )

        from unittest.mock import Mock, patch

        from api.views.fpo_catalogue_requests import _send_request_email

        with patch("api.views.fpo_catalogue_requests.requests.post", return_value=Mock(status_code=202)) as send:
            _send_request_email(request)

        args, kwargs = send.call_args
        self.assertEqual(args[0], "https://api.sendgrid.com/v3/mail/send")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["json"]["personalizations"][0]["to"], [{"email": "fpo@example.com"}])
        self.assertIn("Open Approval Cycle", kwargs["json"]["content"][1]["value"])
        self.assertIn(self.payload["request_comment"], kwargs["json"]["content"][0]["value"])
        self.assertIn(self.payload["request_comment"], kwargs["json"]["content"][1]["value"])

    def test_multi_entry_submission_creates_one_email_and_shared_batch(self):
        from unittest.mock import patch

        entries = [
            {"l1": "New L1", "l2": "New L2", "l3": "New L3", "l4": "New L4"},
            {"l1": "New L1", "l2": "New L2", "l3": "New L3", "l4": "Another L4"},
        ]
        payload = {"product": "LCL", "entries": entries, "request_comment": self.payload["request_comment"]}
        with patch("api.views.fpo_catalogue_requests._send_request_batch_email") as send:
            response = self.client.post(self.request_url, payload, format="json")

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(set(FpoCatalogueRequest.objects.filter(batch_id=response.data["batch_id"]).values_list("batch_id", flat=True))), 1)
        self.assertEqual(FpoCatalogueRequest.objects.filter(batch_id=response.data["batch_id"]).count(), 2)
        send.assert_called_once()

    def test_invalid_entry_prevents_any_batch_rows(self):
        entries = [
            {"l1": "New L1", "l2": "New L2", "l3": "New L3", "l4": "New L4"},
            {"l1": "New L1", "l2": "", "l3": "New L3", "l4": "Another L4"},
        ]
        response = self.client.post(
            self.request_url,
            {"product": "LCL", "entries": entries, "request_comment": self.payload["request_comment"]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(FpoCatalogueRequest.objects.count(), 0)

    def test_batch_approval_inserts_all_entries_and_updates_all_rows(self):
        from unittest.mock import patch

        batch_id = "9ef6a3f9-915a-4c0f-b746-c38526e27f1b"
        requests = [
            FpoCatalogueRequest.objects.create(
                project=self.project,
                batch_id=batch_id,
                requested_by="owner@example.com",
                approver_email="fpo@example.com",
                **{**self.payload, "l4": f"New L4 {index}"},
            )
            for index in (1, 2)
        ]
        edited_entries = [
            {"id": requests[0].pk, "product": "General LCL", "l1": "FPO L1", "l2": "FPO L2", "l3": "FPO L3", "l4": "FPO L4 A"},
            {"id": requests[1].pk, "product": "LCL", "l1": "FPO L1", "l2": "FPO L2", "l3": "FPO L3", "l4": "FPO L4 B"},
        ]
        self.client.credentials(HTTP_X_USER_EMAIL="fpo@example.com")
        with patch("api.views.fpo_catalogue_requests._send_decision_batch_email") as send:
            response = self.client.post(
                "/api/approval-cycle/fpo-requests/batch-decision/",
                {"batch_id": batch_id, "action": "approved", "comment": "Approved", "entries": edited_entries},
                format="json",
            )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["rows"]), 2)
        self.assertEqual(FpoCatalogueRequest.objects.filter(batch_id=batch_id, status="approved").count(), 2)
        for request, entry in zip(requests, edited_entries):
            request.refresh_from_db()
            expected = ("LCL", entry["l1"], entry["l2"], entry["l3"], entry["l4"])
            self.assertEqual((request.product, request.l1, request.l2, request.l3, request.l4), expected)
        self.assertEqual(ServiceCatalogue.objects.filter(l1="FPO L1", l2="FPO L2", l3="FPO L3").count(), 2)
        send.assert_called_once()

    def test_duplicate_fpo_edits_leave_batch_pending_and_do_not_insert(self):
        batch_id = "4ad483da-23c1-4ad7-968d-88794af564be"
        requests = [
            FpoCatalogueRequest.objects.create(
                project=self.project,
                batch_id=batch_id,
                requested_by="owner@example.com",
                approver_email="fpo@example.com",
                **{**self.payload, "l4": f"Original {index}"},
            )
            for index in (1, 2)
        ]
        duplicate_entries = [
            {"id": request.pk, "product": "LCL", "l1": "Edited", "l2": "Edited", "l3": "Edited", "l4": "Edited"}
            for request in requests
        ]
        self.client.credentials(HTTP_X_USER_EMAIL="fpo@example.com")
        response = self.client.post(
            "/api/approval-cycle/fpo-requests/batch-decision/",
            {"batch_id": batch_id, "action": "approved", "comment": "Approved", "entries": duplicate_entries},
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(FpoCatalogueRequest.objects.filter(batch_id=batch_id, status="pending").count(), 2)
        self.assertFalse(ServiceCatalogue.objects.filter(l1="Edited", l2="Edited", l3="Edited", l4="Edited").exists())

    def test_batch_rejection_updates_all_rows_without_catalogue_insert(self):
        from unittest.mock import patch

        batch_id = "23a12712-89b5-48a5-bfec-2cc3408d5f31"
        for index in (1, 2):
            FpoCatalogueRequest.objects.create(
                project=self.project,
                batch_id=batch_id,
                requested_by="owner@example.com",
                approver_email="fpo@example.com",
                **{**self.payload, "l4": f"New L4 {index}"},
            )
        self.client.credentials(HTTP_X_USER_EMAIL="fpo@example.com")
        with patch("api.views.fpo_catalogue_requests._send_decision_batch_email"):
            response = self.client.post(
                "/api/approval-cycle/fpo-requests/batch-decision/",
                {"batch_id": batch_id, "action": "rejected", "comment": "Not enough detail"},
                format="json",
            )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(FpoCatalogueRequest.objects.filter(batch_id=batch_id, status="rejected").count(), 2)
        self.assertEqual(FpoCatalogueRequest.objects.filter(batch_id=batch_id, decision_comment="Not enough detail").count(), 2)
        self.assertFalse(ServiceCatalogue.objects.filter(l4__startswith="New L4 ").exists())