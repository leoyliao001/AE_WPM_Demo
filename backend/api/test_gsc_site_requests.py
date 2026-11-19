from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from api.models import (
    GscSiteRequest,
    MigrationIntakeSubmission,
    MigrationTeam,
    StakeholderRegistration,
)


class GscSiteRequestTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="GSC-REQUEST-TEST",
            requestor="owner@example.com",
            project_name="GSC request test",
            region="APA",
            areas=["China"],
            default_location_strategies=["Chengdu"],
        )
        self.manager = MigrationTeam.objects.create(
            role="Manager",
            email="manager@example.com",
        )
        StakeholderRegistration.objects.create(
            project=self.project,
            team_members=[
                {
                    "id": f"migration-team-{self.manager.pk}",
                    "fullName": "Migration Manager",
                    "email": "manager@example.com",
                }
            ],
            assignments={
                "migration_manager": {
                    "personIds": [f"migration-team-{self.manager.pk}"],
                    "lockedAt": "2026-11-19",
                }
            },
        )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.request_url = (
            f"/api/migration-dashboard/projects/{self.project.pk}/resources/"
            "gsc-site-requests/"
        )
        self.payload = {
            "sites": ["Brazil"],
            "request_comment": "The project requires an additional delivery site.",
        }

    def create_request(self):
        with patch("api.views.gsc_site_requests._send_request_batch_email") as send:
            response = self.client.post(self.request_url, self.payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        send.assert_called_once()
        return response

    def test_request_and_approval_adds_site_only_to_project_resources_options(self):
        resources = self.client.get(
            f"/api/migration-dashboard/projects/{self.project.pk}/resources/"
        ).data
        self.assertEqual(resources["sites"], ["Chengdu"])
        self.assertNotIn("Brazil", resources["gscSiteOptions"])
        self.assertIn("Chengdu", resources["gscSiteRequestOptions"])
        self.assertIn("Brazil", resources["gscSiteRequestOptions"])

        response = self.create_request()
        request_id = response.data["gsc_request_id"]
        item = GscSiteRequest.objects.get(pk=request_id)
        self.assertEqual(item.approver_emails, ["manager@example.com"])
        self.assertEqual(item.status, "pending")

        self.client.credentials(HTTP_X_USER_EMAIL="manager@example.com")
        queue = self.client.get("/api/approval-cycle/queue/?scope=mine").data
        queued = next(
            row for row in queue["rows"] if row["request_kind"] == "gsc_site"
        )
        self.assertTrue(queued["actionable"])
        with patch("api.views.gsc_site_requests._send_decision_email") as send:
            decision = self.client.post(
                f"/api/approval-cycle/gsc-site-requests/{request_id}/decision/",
                {"action": "approved", "comment": "Approved for this project."},
                format="json",
            )
        self.assertEqual(decision.status_code, 200, decision.data)
        send.assert_called_once()

        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        resources = self.client.get(
            f"/api/migration-dashboard/projects/{self.project.pk}/resources/"
        ).data
        self.assertIn("Brazil", resources["gscSiteOptions"])
        self.assertEqual(resources["gscSiteRequests"][0]["status"], "approved")

    def test_rejected_site_is_not_added_to_resources_options(self):
        response = self.create_request()
        request_id = response.data["gsc_request_id"]
        self.client.credentials(HTTP_X_USER_EMAIL="manager@example.com")
        with patch("api.views.gsc_site_requests._send_decision_email"):
            decision = self.client.post(
                f"/api/approval-cycle/gsc-site-requests/{request_id}/decision/",
                {"action": "rejected", "comment": "Use an existing site."},
                format="json",
            )
        self.assertEqual(decision.status_code, 200, decision.data)

        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        resources = self.client.get(
            f"/api/migration-dashboard/projects/{self.project.pk}/resources/"
        ).data
        self.assertNotIn("Brazil", resources["gscSiteOptions"])
        self.assertEqual(resources["gscSiteRequests"][0]["status"], "rejected")

    def test_duplicate_pending_and_unauthorised_decision_are_rejected(self):
        response = self.create_request()
        duplicate = self.client.post(self.request_url, self.payload, format="json")
        self.assertEqual(duplicate.status_code, 409)

        self.client.credentials(HTTP_X_USER_EMAIL="other@example.com")
        decision = self.client.post(
            f"/api/approval-cycle/gsc-site-requests/{response.data['gsc_request_id']}/decision/",
            {"action": "approved"},
            format="json",
        )
        self.assertEqual(decision.status_code, 403)

    def test_multiple_intake_sites_create_separate_project_requests(self):
        payload = {
            **self.payload,
            "sites": ["Brazil", "Chongqing"],
        }
        with patch("api.views.gsc_site_requests._send_request_batch_email") as send:
            response = self.client.post(self.request_url, payload, format="json")

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(
            set(GscSiteRequest.objects.values_list("site", flat=True)),
            {"Brazil", "Chongqing"},
        )
        send.assert_called_once()

    def test_request_rejects_sites_outside_intake_options(self):
        response = self.client.post(
            self.request_url,
            {**self.payload, "sites": ["Not a Strategic Location"]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Migration Intake", response.data["error"])

    @override_settings(
        SENDGRID_API_KEY="test-key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        DJANGO_PUBLIC_BASE_URL="https://wpmpulse.crb.apmoller.net",
    )
    def test_sendgrid_request_email_contains_direct_approval_links(self):
        from unittest.mock import Mock, patch
        from api.views.gsc_site_requests import _send_request_batch_email

        response = self.create_request()
        item = GscSiteRequest.objects.get(pk=response.data["gsc_request_id"])
        with patch(
            "api.views.gsc_site_requests.requests.post",
            return_value=Mock(status_code=202),
        ) as send:
            _send_request_batch_email([item])

        request = send.call_args.kwargs["json"]
        direct_url = f"https://wpmpulse.crb.apmoller.net/approval-cycle?gsc_request={item.pk}"
        self.assertEqual(
            request["personalizations"][0]["to"],
            [{"email": "manager@example.com"}],
        )
        self.assertIn(direct_url, request["content"][0]["value"])
        self.assertIn(direct_url, request["content"][1]["value"])
        self.assertIn("GSC Site approval required", request["content"][1]["value"])

    @override_settings(
        SENDGRID_API_KEY="test-key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        DJANGO_PUBLIC_BASE_URL="https://wpmpulse.crb.apmoller.net",
    )
    def test_sendgrid_decision_email_contains_direct_review_link(self):
        from unittest.mock import Mock, patch
        from api.views.gsc_site_requests import _send_decision_email

        item = GscSiteRequest.objects.create(
            project=self.project,
            site="Brazil",
            requested_by="owner@example.com",
            approver_emails=["manager@example.com"],
            request_comment="Need additional coverage.",
            status="approved",
            decision_comment="Approved for this project.",
            decided_by="manager@example.com",
        )
        with patch(
            "api.views.gsc_site_requests.requests.post",
            return_value=Mock(status_code=202),
        ) as send:
            _send_decision_email(item)

        request = send.call_args.kwargs["json"]
        direct_url = f"https://wpmpulse.crb.apmoller.net/approval-cycle?gsc_request={item.pk}"
        self.assertEqual(
            request["personalizations"][0]["to"],
            [{"email": "owner@example.com"}],
        )
        self.assertIn(direct_url, request["content"][0]["value"])
        self.assertIn(direct_url, request["content"][1]["value"])
        self.assertIn("Approved", request["content"][1]["value"])
