from django.test import TestCase
from rest_framework.test import APIClient

from api.models import BauControlAgreement, MigrationIntakeSubmission, ProjectAttributesAccess


class BauControlsTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="BAU-CONTROLS-TEST",
            requested_date="2026-11-26",
            requestor="owner@example.com",
            project_name="BAU Controls test",
            migration_type="1:1 Transfer",
            migration_type_value="1:1-transfer",
            region="APA",
            function_name="Ocean",
            products=["Ocean"],
            proposed_scope="Test",
            fte_number="1",
        )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.project_url = f"/api/migration-dashboard/projects/{self.project.pk}/bau-controls/"
        self.admin_url = "/api/migration-dashboard/bau-controls/"
        self.payload = {
            "migrationName": self.project.project_name,
            "product": "Ocean",
            "area": "APA",
            "reviewCadence": "Monthly",
            "workingCadence": "As needed",
            "areaAccepted": False,
            "gscAccepted": False,
        }

    def test_project_can_save_draft_and_confirm_only_after_both_accept(self):
        saved = self.client.post(self.project_url, self.payload, format="json")
        self.assertEqual(saved.status_code, 201, saved.data)
        self.assertEqual(saved.data["agreement"]["status"], "draft")

        loaded = self.client.get(self.project_url)
        self.assertEqual(loaded.status_code, 200, loaded.data)
        self.assertTrue(loaded.data["saved"])
        self.assertEqual(loaded.data["agreement"]["product"], "Ocean")

        partial_acceptance = {
            **self.payload,
            "areaAccepted": True,
            "action": "confirm",
        }
        rejected = self.client.post(self.project_url, partial_acceptance, format="json")
        self.assertEqual(rejected.status_code, 400, rejected.data)
        self.assertEqual(BauControlAgreement.objects.get(project=self.project).status, "draft")

        confirmed = self.client.post(
            self.project_url,
            {**self.payload, "areaAccepted": True, "gscAccepted": True, "action": "confirm"},
            format="json",
        )
        self.assertEqual(confirmed.status_code, 200, confirmed.data)
        self.assertEqual(confirmed.data["agreement"]["status"], "confirmed")
        self.assertEqual(confirmed.data["agreement"]["confirmedBy"], "owner@example.com")

    def test_project_access_and_validation_are_enforced(self):
        self.client.credentials(HTTP_X_USER_EMAIL="other@example.com")
        self.assertEqual(self.client.get(self.project_url).status_code, 403)
        self.assertEqual(
            self.client.post(
                self.project_url,
                {**self.payload, "reviewCadence": "Never"},
                format="json",
            ).status_code,
            403,
        )

        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        invalid_date = {**self.payload, "effectiveFrom": "not-a-date"}
        self.assertEqual(self.client.post(self.project_url, invalid_date, format="json").status_code, 400)
        self.assertFalse(BauControlAgreement.objects.exists())

    def test_admin_can_create_update_list_and_delete_agreements(self):
        self.client.credentials(HTTP_X_USER_EMAIL="maintainer@example.com")
        self.assertEqual(self.client.get(self.admin_url).status_code, 403)
        ProjectAttributesAccess.objects.create(
            email="maintainer@example.com",
            bau_control_agreement=True,
        )

        created = self.client.post(
            self.admin_url,
            {**self.payload, "projectId": self.project.pk},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        agreement_id = created.data["agreement"]["id"]
        self.assertEqual(created.data["agreement"]["createdBy"], "maintainer@example.com")

        duplicate = self.client.post(
            self.admin_url,
            {**self.payload, "projectId": self.project.pk},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 409)

        listed = self.client.get(self.admin_url)
        self.assertEqual(listed.status_code, 200, listed.data)
        self.assertEqual(listed.data["count"], 1)
        self.assertEqual(listed.data["rows"][0]["projectName"], self.project.project_name)

        updated = self.client.put(
            f"{self.admin_url}{agreement_id}/",
            {
                **self.payload,
                "projectId": self.project.pk,
                "areaAccepted": True,
                "gscAccepted": True,
                "action": "confirm",
                "areaNameRole": "Area owner",
                "gscNameRole": "GSC owner",
            },
            format="json",
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data["agreement"]["status"], "confirmed")
        self.assertEqual(updated.data["agreement"]["updatedBy"], "maintainer@example.com")

        deleted = self.client.delete(f"{self.admin_url}{agreement_id}/")
        self.assertEqual(deleted.status_code, 200, deleted.data)
        self.assertFalse(BauControlAgreement.objects.exists())

    def test_access_control_grid_includes_bau_controls(self):
        self.client.credentials(HTTP_X_USER_EMAIL="maintainer@example.com")
        ProjectAttributesAccess.objects.create(
            email="maintainer@example.com",
            bau_control_agreement=True,
            access_control=True,
        )
        response = self.client.get("/api/project-attributes-access/")
        self.assertEqual(response.status_code, 200, response.data)
        row = next(item for item in response.data["rows"] if item["email"] == "maintainer@example.com")
        self.assertIn(
            {"key": "bau_control_agreement", "label": "BAU Controls (Y/N)"},
            response.data["columns"],
        )
        self.assertEqual(row["bau_control_agreement"], "Y")
