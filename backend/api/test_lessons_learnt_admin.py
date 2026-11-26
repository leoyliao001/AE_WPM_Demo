from django.test import TestCase
from rest_framework.test import APIClient

from api.models import LessonLearnt, MigrationIntakeSubmission, ProjectAttributesAccess


class LessonsLearntAdminTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="LESSONS-ADMIN-TEST",
            requested_date="2026-11-26",
            requestor="owner@example.com",
            project_name="Lessons admin test",
            migration_type="1:1 Transfer",
            migration_type_value="1:1-transfer",
            region="APA",
            function_name="Ocean",
            products=["Ocean"],
            proposed_scope="Test",
            fte_number="1",
        )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL="maintainer@example.com")
        self.url = "/api/migration-dashboard/lessons-learnt/"
        self.payload = {
            "projectId": self.project.pk,
            "happened": "The project handover missed an owner.",
            "learned": "Confirm ownership before transition.",
            "nextTime": "Review the checklist with each owner.",
            "type": "Improve",
            "phase": "Close",
            "relatedArtefact": "Sign-off",
            "relevantFor": "Similar migrations",
        }

    def grant_access(self):
        ProjectAttributesAccess.objects.create(
            email="maintainer@example.com",
            lessons_learnt=True,
        )

    def test_requires_lessons_learnt_table_access(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 403)
        self.assertFalse(LessonLearnt.objects.exists())

    def test_admin_can_create_update_list_and_delete_records(self):
        self.grant_access()

        created = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        first_id = created.data["lesson"]["id"]
        self.assertEqual(created.data["lesson"]["createdBy"], "maintainer@example.com")

        duplicate = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(duplicate.status_code, 201, duplicate.data)
        second_id = duplicate.data["lesson"]["id"]
        self.assertEqual(LessonLearnt.objects.filter(project=self.project).count(), 2)

        listed = self.client.get(self.url)
        self.assertEqual(listed.status_code, 200, listed.data)
        self.assertEqual(listed.data["count"], 2)
        self.assertEqual(listed.data["rows"][0]["projectName"], self.project.project_name)

        updated_payload = {**self.payload, "happened": "Updated by an administrator."}
        updated = self.client.put(
            f"{self.url}{first_id}/",
            updated_payload,
            format="json",
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data["lesson"]["happened"], updated_payload["happened"])

        deleted = self.client.delete(f"{self.url}{second_id}/")
        self.assertEqual(deleted.status_code, 200, deleted.data)
        self.assertFalse(LessonLearnt.objects.filter(pk=second_id).exists())
        self.assertEqual(LessonLearnt.objects.filter(project=self.project).count(), 1)

    def test_invalid_project_and_lesson_payloads_are_rejected(self):
        self.grant_access()

        invalid_lesson = {**self.payload, "phase": "Not a phase"}
        self.assertEqual(self.client.post(self.url, invalid_lesson, format="json").status_code, 400)

        missing_project = {**self.payload, "projectId": 999999}
        self.assertEqual(self.client.post(self.url, missing_project, format="json").status_code, 404)
        self.assertFalse(LessonLearnt.objects.exists())

    def test_access_control_grid_exposes_lessons_learnt_permission(self):
        ProjectAttributesAccess.objects.create(
            email="maintainer@example.com",
            lessons_learnt=True,
            access_control=True,
        )

        response = self.client.get(
            "/api/project-attributes-access/",
        )

        self.assertEqual(response.status_code, 200, response.data)
        row = next(item for item in response.data["rows"] if item["email"] == "maintainer@example.com")
        self.assertIn(
            {"key": "lessons_learnt", "label": "Lessons Learnt (Y/N)"},
            response.data["columns"],
        )
        self.assertEqual(row["lessons_learnt"], "Y")
