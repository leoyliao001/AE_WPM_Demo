from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from api.models import FpoCatalogueRequest, MigrationIntakeSubmission, ServiceCatalogue


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
        }

    def test_reminder_persists_until_approved_hierarchy_is_acknowledged(self):
        with self.settings(FPO_CATALOGUE_APPROVER_EMAIL="fpo@example.com"):
            from unittest.mock import patch

            with patch("api.views.fpo_catalogue_requests._send_request_email"):
                response = self.client.post(self.request_url, self.payload, format="json")

        self.assertEqual(response.status_code, 201, response.data)
        request = FpoCatalogueRequest.objects.get(pk=response.data["id"])
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

    def test_approval_inserts_and_exposes_catalogue_entry(self):
        request = FpoCatalogueRequest.objects.create(
            project=self.project,
            requested_by="owner@example.com",
            approver_email="fpo@example.com",
            **self.payload,
        )
        self.client.credentials(HTTP_X_USER_EMAIL="fpo@example.com")
        response = self.client.post(
            f"/api/approval-cycle/fpo-requests/{request.pk}/decision/",
            {"action": "approved", "comment": "Approved"},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(ServiceCatalogue.objects.filter(
            product="LCL", l1="New L1", l2="New L2", l3="New L3", l4="New L4"
        ).exists())

        from api.views.opportunity_task_scope import _catalogue, _catalogue_additions

        _catalogue.cache_clear()
        _catalogue_additions.cache_clear()
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        additions = self.client.get(self.scope_url).data["catalogue_additions"]
        self.assertIn(["LCL", "New L1", "New L2", "New L3", "New L4", "", "", "", "New L4"], additions)

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