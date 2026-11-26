from django.test import TestCase
from rest_framework.test import APIClient

from api.models import LessonLearnt, MigrationIntakeSubmission


class LessonsLearntTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="LESSONS-TEST",
            requested_date="2026-11-26",
            requestor="owner@example.com",
            project_name="Lessons test",
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
        self.url = f"/api/migration-dashboard/projects/{self.project.pk}/lessons-learnt/"
        self.lesson = {
            "happened": "The transition checklist was incomplete.",
            "learned": "Confirm owners before the handover.",
            "nextTime": "Review the checklist with each owner.",
            "type": "Improve",
            "phase": "Close",
            "relatedArtefact": "Sign-off",
            "relevantFor": "Similar migrations",
        }

    def test_create_and_read_project_lesson(self):
        created = self.client.post(self.url, self.lesson, format="json")

        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["lesson"]["happened"], self.lesson["happened"])
        self.assertEqual(created.data["lesson"]["createdBy"], "owner@example.com")
        self.assertEqual(LessonLearnt.objects.get().project, self.project)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["saved"])
        self.assertEqual(response.data["lesson"]["relevantFor"], "Similar migrations")

    def test_invalid_and_unauthorized_requests_are_rejected(self):
        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, 400)
        invalid = {**self.lesson, "type": "Unknown"}
        self.assertEqual(self.client.post(self.url, invalid, format="json").status_code, 400)
        self.assertFalse(LessonLearnt.objects.exists())

        self.client.credentials(HTTP_X_USER_EMAIL="outsider@example.com")
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, self.lesson, format="json").status_code, 403)

    def test_project_lesson_cannot_be_submitted_twice(self):
        first = self.client.post(self.url, self.lesson, format="json")
        self.assertEqual(first.status_code, 201, first.data)

        repeated = self.client.post(self.url, self.lesson, format="json")

        self.assertEqual(repeated.status_code, 409)
        self.assertEqual(repeated.data["lesson"]["id"], first.data["lesson"]["id"])
        self.assertEqual(LessonLearnt.objects.filter(project=self.project).count(), 1)
