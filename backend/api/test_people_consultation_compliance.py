from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from api.models import MigrationIntakeSubmission, PeopleConsultationCompliance


class PeopleConsultationComplianceTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="PEOPLE-CHECK-1",
            requestor="owner@example.com",
            project_name="People checklist test",
            fte_number="1",
            region="EUR",
            areas=["EME"],
            countries=["Egypt"],
            products=["General Ocean"],
        )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.url = f"/api/migration-dashboard/projects/{self.project.pk}/people-consultation-compliance/"
        self.evidence_url = self.url + "evidence/"
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.media_settings = override_settings(MEDIA_ROOT=self.media.name)
        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)

    def test_initial_catalogue_confirm_freeze_and_reopen(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["saved"])
        self.assertEqual(len(response.data["items"]), 8)

        response = self.client.post(self.url, {
            "action": "confirm",
            "revision": 0,
            "items": response.data["items"],
        }, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "confirmed")
        self.assertEqual(response.data["version"], 1)
        self.assertEqual(response.data["items"][0]["status"], "not_started")
        self.assertEqual(response.data["auditLog"][-1]["field"], "status")
        self.assertTrue(PeopleConsultationCompliance.objects.filter(project=self.project).exists())

        frozen = self.client.post(self.url, {
            "action": "save",
            "revision": response.data["revision"],
            "items": response.data["items"],
        }, format="json")
        self.assertEqual(frozen.status_code, 409)

        missing_reason = self.client.post(self.url, {
            "action": "reopen",
            "revision": response.data["revision"],
            "reason": "  ",
        }, format="json")
        self.assertEqual(missing_reason.status_code, 400)

        reopened = self.client.post(self.url, {
            "action": "reopen",
            "revision": response.data["revision"],
            "reason": "Update consultation evidence",
        }, format="json")
        self.assertEqual(reopened.status_code, 200, reopened.data)
        self.assertEqual(reopened.data["status"], "draft")
        self.assertEqual(reopened.data["version"], 2)
        self.assertEqual(reopened.data["auditLog"][-1]["reason"], "Update consultation evidence")

    def test_not_applicable_requires_reason_and_changes_are_audited(self):
        initial = self.client.get(self.url).data
        items = initial["items"]
        items[0]["applicable"] = False
        invalid = self.client.post(self.url, {
            "action": "save", "revision": 0, "items": items,
        }, format="json")
        self.assertEqual(invalid.status_code, 400)

        items[0]["reason"] = "No employees are in scope."
        saved = self.client.post(self.url, {
            "action": "save", "revision": 0, "items": items,
        }, format="json")
        self.assertEqual(saved.status_code, 200, saved.data)
        self.assertEqual(saved.data["items"][0]["status"], "not_applicable")
        self.assertTrue(any(
            entry["field"] == "applicable" and entry["new"] is False
            for entry in saved.data["auditLog"]
        ))

    def test_revision_conflict_preserves_saved_record(self):
        initial = self.client.get(self.url).data
        saved = self.client.post(self.url, {
            "action": "save", "revision": 0, "items": initial["items"],
        }, format="json")
        self.assertEqual(saved.status_code, 200)
        stale = self.client.post(self.url, {
            "action": "save", "revision": 0, "items": initial["items"],
        }, format="json")
        self.assertEqual(stale.status_code, 409)

    def test_evidence_upload_download_delete_and_revision_guard(self):
        initial = self.client.get(self.url).data
        saved = self.client.post(self.url, {
            "action": "save", "revision": 0, "items": initial["items"],
        }, format="json")
        self.assertEqual(saved.status_code, 200)

        stale_upload = self.client.post(self.evidence_url, {
            "itemId": initial["items"][0]["id"],
            "revision": "0",
            "file": SimpleUploadedFile("notice.pdf", b"evidence", content_type="application/pdf"),
        })
        self.assertEqual(stale_upload.status_code, 409)

        uploaded = self.client.post(self.evidence_url, {
            "itemId": initial["items"][0]["id"],
            "revision": str(saved.data["revision"]),
            "file": SimpleUploadedFile("notice.pdf", b"evidence", content_type="application/pdf"),
        })
        self.assertEqual(uploaded.status_code, 200, uploaded.data)
        attachment = uploaded.data["items"][0]["evidenceFiles"][0]
        self.assertEqual(attachment["name"], "notice.pdf")
        download = self.client.get(attachment["url"])
        self.assertEqual(download.status_code, 200)
        self.assertEqual(b"".join(download.streaming_content), b"evidence")

        removed = self.client.delete(self.evidence_url, {
            "evidenceId": attachment["id"], "revision": uploaded.data["revision"],
        }, format="json")
        self.assertEqual(removed.status_code, 200, removed.data)
        self.assertEqual(removed.data["items"][0]["evidenceFiles"], [])

        uploaded_again = self.client.post(self.evidence_url, {
            "itemId": initial["items"][0]["id"],
            "revision": str(removed.data["revision"]),
            "file": SimpleUploadedFile("notice.pdf", b"evidence", content_type="application/pdf"),
        })
        self.assertEqual(uploaded_again.status_code, 200, uploaded_again.data)
        items = uploaded_again.data["items"]
        items[0]["status"] = "confirmed"
        items[0]["statusDate"] = "2026-11-05"
        confirmed = self.client.post(self.url, {
            "action": "confirm",
            "revision": uploaded_again.data["revision"],
            "items": items,
        }, format="json")
        self.assertEqual(confirmed.status_code, 200, confirmed.data)
        self.assertEqual(confirmed.data["items"][0]["status"], "confirmed")
