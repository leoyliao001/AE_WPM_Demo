from django.test import TestCase
from rest_framework.test import APIClient

from api.models import MigrationIntakeSubmission, ProjectAttributesAccess
from api.permissions.attributes_access import TABLE_KEYS, build_access_snapshot


class SuperAdminAccessTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="SUPER-ADMIN-ACCESS-TEST",
            requested_date="2026-10-27", requestor="owner@example.com",
            project_name="Admin access test", migration_type="1:1 Transfer",
            migration_type_value="1:1-transfer", region="APA",
            function_name="Customer Experience", products=["General Ocean"],
            proposed_scope="Test scope", fte_number="1",
        )
        self.admin = "admin@example.com"
        ProjectAttributesAccess.objects.create(email=self.admin, is_super_admin=True)
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL=self.admin)
        self.base = f"/api/migration-dashboard/projects/{self.project.pk}/"

    def test_super_admin_has_every_table_permission_without_individual_flags(self):
        snapshot = build_access_snapshot(self.admin)
        self.assertTrue(snapshot["is_super_admin"])
        self.assertEqual(snapshot["tables"], dict.fromkeys(TABLE_KEYS, True))
        for page in (
            "opportunity-assessment", "scope-statement", "stakeholder-registration",
            "project-charter", "business-case",
        ):
            with self.subTest(page=page):
                response = self.client.get(f"{self.base}{page}/")
                self.assertEqual(response.status_code, 200, response.data)

    def test_super_admin_can_save_another_requestors_opportunity_assessment(self):
        response = self.client.post(
            f"{self.base}opportunity-assessment/data/",
            {"uniqueData": [{"task_name": "Admin task"}]}, format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["created_count"], 1)
        self.assertEqual(response.data["error_count"], 0)

    def test_non_super_admin_cannot_manage_another_requestors_assessment(self):
        ProjectAttributesAccess.objects.create(
            email="maintainer@example.com", migration_intake=True, access_control=True,
        )
        self.client.credentials(HTTP_X_USER_EMAIL="maintainer@example.com")
        for method, path, payload in (
            ("get", "opportunity-assessment/", None),
            ("post", "opportunity-assessment/data/", {"uniqueData": [{"task_name": "Denied"}]}),
            ("delete", "opportunity-assessment/data/delete/", {"ids": [1]}),
        ):
            with self.subTest(path=path):
                response = (
                    self.client.get(self.base + path) if payload is None else
                    getattr(self.client, method)(self.base + path, payload, format="json")
                )
                self.assertEqual(response.status_code, 403, response.data)

    def test_super_admin_can_assign_stakeholders_but_cannot_edit_locked_roles(self):
        url = f"{self.base}stakeholder-registration/save/"
        payload = {
            "action": "save",
            "teamMembers": [{"id": "test-person", "fullName": "Test Person", "email": "person@example.com"}],
            "assignments": {
                code: {"personIds": ["test-person"]}
                for code in ("project_sponsor", "area_sme", "gsc_sme")
            },
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(all(response.data["assignmentPermissions"].values()))
        response = self.client.post(url, {"action": "lock", "roleCode": "project_sponsor"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        payload["assignments"]["project_sponsor"]["personIds"] = []
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 409, response.data)
        response = self.client.post(url, {"action": "unlock", "roleCode": "project_sponsor"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 200, response.data)

    def test_non_super_admin_still_needs_designated_stakeholder_assigner(self):
        ProjectAttributesAccess.objects.create(email="maintainer@example.com", stakeholder_registration=True)
        self.client.credentials(HTTP_X_USER_EMAIL="maintainer@example.com")
        response = self.client.post(
            f"{self.base}stakeholder-registration/save/",
            {
                "teamMembers": [{"id": "test-person", "fullName": "Test Person", "email": "person@example.com"}],
                "assignments": {"project_sponsor": {"personIds": ["test-person"]}},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403, response.data)
