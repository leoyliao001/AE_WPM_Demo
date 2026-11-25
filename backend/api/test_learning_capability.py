import json
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from api.models import (
    LearningCapabilityRecord,
    MigrationIntakeSubmission,
    MigrationTeam,
    ProjectAttributesAccess,
    StakeholderRegistration,
)


class LearningCapabilityTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="LD-TEST",
            requested_date="2026-01-01",
            requestor="owner@example.com",
            project_name="L&D test project",
            migration_type="Full",
            migration_type_value="Full migration",
            region="EUR",
            function_name="Finance",
            proposed_scope="Project scope",
            fte_number="1",
        )
        self.manager = MigrationTeam.objects.create(role="Manager", email="manager@example.com")
        StakeholderRegistration.objects.create(
            project=self.project,
            team_members=[{"id": "member-1", "email": "member@example.com"}],
            assignments={
                "migration_manager": {
                    "personIds": [f"migration-team-{self.manager.pk}"],
                    "lockedAt": "2026-01-01",
                },
            },
        )
        self.client = APIClient()
        self.url = f"/api/migration-dashboard/projects/{self.project.pk}/learning-capability/"

    def state(self):
        return {
            "plans": {"Wave 1": {"start": "2026-01-01", "fdays": "2", "trainer": "Trainer"}},
            "kt": {"Wave 1": {"Order|Create": {"deliveredBy": "Area", "material": "Ready"}}},
            "scores": {"Wave 1": [{"name": "FTE 1", "kt": "90", "foundation": "90"}]},
            "processCount": 1,
        }

    def test_only_assigned_migration_manager_and_super_admin_can_save(self):
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.assertEqual(self.client.get(self.url).status_code, 200)
        denied = self.client.put(
            self.url,
            {"revision": 0, "state": self.state()},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)

        MigrationTeam.objects.create(role="Manager", email="unassigned@example.com")
        self.client.credentials(HTTP_X_USER_EMAIL="unassigned@example.com")
        unassigned = self.client.put(
            self.url,
            {"revision": 0, "state": self.state()},
            format="json",
        )
        self.assertEqual(unassigned.status_code, 403)

        self.client.credentials(HTTP_X_USER_EMAIL="manager@example.com")
        saved = self.client.put(
            self.url,
            {"revision": 0, "state": self.state()},
            format="json",
        )
        self.assertEqual(saved.status_code, 200, saved.data)
        self.assertEqual(saved.data["revision"], 1)
        self.assertEqual(saved.data["state"], self.state())
        self.assertEqual(LearningCapabilityRecord.objects.get(project=self.project).updated_by, "manager@example.com")

    def test_stale_revision_is_rejected_without_overwriting_saved_state(self):
        self.client.credentials(HTTP_X_USER_EMAIL="manager@example.com")
        first = self.client.put(self.url, {"revision": 0, "state": self.state()}, format="json")
        self.assertEqual(first.status_code, 200, first.data)
        stale_state = {**self.state(), "plans": {"Wave 2": {}}}
        stale = self.client.put(self.url, {"revision": 0, "state": stale_state}, format="json")
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(
            LearningCapabilityRecord.objects.get(project=self.project).state,
            self.state(),
        )

    def test_evidence_is_stored_in_media_and_downloaded_through_project_access(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.client.credentials(HTTP_X_USER_EMAIL="manager@example.com")
                uploaded = SimpleUploadedFile("training.pdf", b"evidence bytes", content_type="application/pdf")
                response = self.client.put(
                    self.url,
                    {
                        "revision": "0",
                        "state": json.dumps(self.state()),
                        "evidence": uploaded,
                    },
                    format="multipart",
                )
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data["evidence"]["name"], "training.pdf")
                evidence_url = response.data["evidence"]["url"]
                download = self.client.get(evidence_url)
                self.assertEqual(download.status_code, 200)
                self.assertEqual(b"".join(download.streaming_content), b"evidence bytes")

    def test_invalid_learning_state_is_rejected(self):
        self.client.credentials(HTTP_X_USER_EMAIL="manager@example.com")
        response = self.client.put(
            self.url,
            {"revision": 0, "state": {"plans": []}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(LearningCapabilityRecord.objects.exists())

    def test_portfolio_readiness_is_derived_from_database_record(self):
        LearningCapabilityRecord.objects.create(project=self.project, state=self.state())
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        response = self.client.get("/api/migration-dashboard/resources/")
        self.assertEqual(response.status_code, 200, response.data)
        summary = response.data["rows"][0]["learningSummary"]
        self.assertEqual(summary["stages"], [100, 100, 100, 100, 0])
        self.assertEqual(summary["cohorts"], 1)

    def test_super_admin_can_save(self):
        ProjectAttributesAccess.objects.create(email="admin@example.com", is_super_admin=True)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@example.com")
        response = self.client.put(
            self.url,
            {"revision": 0, "state": self.state()},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
