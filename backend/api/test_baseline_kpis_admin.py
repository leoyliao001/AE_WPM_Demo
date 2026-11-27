from django.test import TestCase
from rest_framework.test import APIClient

from api.models import BaselineKpiRecord, MigrationIntakeSubmission, ProjectAttributesAccess


class BaselineKpiAdminTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="KPI-ADMIN-1",
            requested_date="2026-01-01",
            requestor="owner@example.com",
            project_name="Admin KPI project",
            migration_type="Full",
            migration_type_value="Full migration",
            region="EUR",
            areas=["CSE"],
            countries=["Croatia"],
            function_name="Finance",
            proposed_scope="Project scope",
            fte_number="2",
        )
        self.client = APIClient()
        self.url = "/api/baseline-kpis-admin/"

    def grant_access(self, **permissions):
        return ProjectAttributesAccess.objects.create(
            email="admin@example.com",
            **permissions,
        )

    def test_baseline_kpi_admin_permission_is_in_access_snapshot_and_grid(self):
        self.grant_access(baseline_kpis=True, access_control=True)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@example.com")

        access = self.client.get("/api/project-attributes-access/me/")
        self.assertTrue(access.data["tables"]["baseline_kpis"])

        grid = self.client.get("/api/project-attributes-access/")
        self.assertEqual(grid.status_code, 200, grid.data)
        self.assertIn(
            {"key": "baseline_kpis", "label": "Baseline & KPIs (Y/N)"},
            grid.data["columns"],
        )
        row = next(item for item in grid.data["rows"] if item["email"] == "admin@example.com")
        self.assertEqual(row["baseline_kpis"], "Y")

    def test_admin_requires_access(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.credentials(HTTP_X_USER_EMAIL="outsider@example.com")
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(
            self.client.post(
                self.url,
                {"projectId": self.project.pk, "state": {}},
                format="json",
            ).status_code,
            403,
        )

    def test_access_control_can_grant_baseline_kpi_database_permission(self):
        self.grant_access(access_control=True)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@example.com")
        saved = self.client.post(
            "/api/project-attributes-access/data/",
            {
                "uniqueData": [
                    {"email": "maintainer@example.com", "baseline_kpis": "Y"}
                ]
            },
            format="json",
        )
        self.assertEqual(saved.status_code, 200, saved.data)

        self.client.credentials(HTTP_X_USER_EMAIL="maintainer@example.com")
        access = self.client.get("/api/project-attributes-access/me/")
        self.assertTrue(access.data["tables"]["baseline_kpis"])

    def test_create_update_revision_conflict_and_delete_record_without_deleting_project(self):
        self.grant_access(baseline_kpis=True)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@example.com")
        state = {"cohorts": {"Cohort A": {"kpis": []}}}

        created = self.client.post(
            self.url,
            {"projectId": self.project.pk, "state": state},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        record_id = created.data["id"]
        self.assertEqual(created.data["revision"], 1)
        self.assertEqual(created.data["updatedBy"], "admin@example.com")
        projects = self.client.get(self.url).data["projects"]
        self.assertIn(self.project.pk, [project["id"] for project in projects])

        duplicate = self.client.post(
            self.url,
            {"projectId": self.project.pk, "state": {}},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 409)

        update_url = f"{self.url}{record_id}/"
        updated_state = {"cohorts": {}, "updated": True}
        updated = self.client.put(
            update_url,
            {"revision": 1, "state": updated_state},
            format="json",
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data["state"], updated_state)
        self.assertEqual(updated.data["revision"], 2)

        stale = self.client.put(
            update_url,
            {"revision": 1, "state": {}},
            format="json",
        )
        self.assertEqual(stale.status_code, 409)

        deleted = self.client.delete(update_url)
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(BaselineKpiRecord.objects.exists())
        self.assertTrue(MigrationIntakeSubmission.objects.filter(pk=self.project.pk).exists())

    def test_rejects_non_object_state_and_lists_available_projects(self):
        self.grant_access(baseline_kpis=True)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@example.com")

        listing = self.client.get(self.url)
        self.assertEqual(listing.status_code, 200, listing.data)
        self.assertEqual(listing.data["projects"][0]["id"], self.project.pk)

        invalid = self.client.post(
            self.url,
            {"projectId": self.project.pk, "state": []},
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)
