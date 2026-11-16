from copy import deepcopy
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from api.models import MigrationIntakeSubmission


class PeopleConsultationTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="PEOPLE-TEST",
            requested_date="2026-01-01",
            requestor="owner@example.com",
            project_name="People consultation test",
            migration_type="Functional",
            migration_type_value="functional",
            region="EUR",
            function_name="Finance",
            proposed_scope="Test scope",
            fte_number="1",
        )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.url = (
            f"/api/migration-dashboard/projects/{self.project.pk}/"
            "people-consultation-compliance/"
        )

    def get_checklist(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def post_checklist(self, data):
        return self.client.post(self.url, data, format="json")

    def test_initial_catalogue_and_project_access(self):
        data = self.get_checklist()
        self.assertEqual(len(data["items"]), 8)
        self.assertEqual(data["items"][0]["label"], "HR team informed")
        self.client.credentials(HTTP_X_USER_EMAIL="outsider@example.com")
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.credentials()
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_save_confirm_freeze_and_reopen_are_audited(self):
        data = self.get_checklist()
        items = deepcopy(data["items"])
        items[0].update({
            "ownerRole": "HR Business Partner",
            "status": "confirmed",
            "statusDate": "2026-10-08",
            "outcomeNote": "HR team briefed.",
        })
        response = self.post_checklist({
            "revision": data["revision"], "action": "confirm", "items": items,
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["version"], 1)
        confirmed = response.data["items"][0]
        self.assertEqual(confirmed["status"], "confirmed")
        self.assertTrue(confirmed["confirmedAt"])
        self.assertTrue(any(entry["field"] == "owner_role" for entry in confirmed["audit"]))

        updated_items = deepcopy(response.data["items"])
        updated_items[0]["label"] = "Changed after confirmation"
        frozen = self.post_checklist({
            "revision": response.data["revision"], "action": "save", "items": updated_items,
        })
        self.assertEqual(frozen.status_code, 400)

        reopened = self.post_checklist({
            "revision": response.data["revision"],
            "action": "reopen",
            "id": confirmed["id"],
            "reason": "Update the consultation evidence",
        })
        self.assertEqual(reopened.status_code, 200, reopened.data)
        self.assertEqual(reopened.data["items"][0]["status"], "in_progress")
        self.assertEqual(reopened.data["auditLog"][0]["reason"], "Update the consultation evidence")

    def test_not_applicable_requires_reason_and_confirmation_requires_evidence(self):
        data = self.get_checklist()
        items = deepcopy(data["items"])
        items[0].update({"applicable": False, "status": "not_applicable"})
        response = self.post_checklist({
            "revision": data["revision"], "action": "save", "items": items,
        })
        self.assertEqual(response.status_code, 400)
        items[0]["naReason"] = "No critical roles are leaving the area."
        items[0].update({"applicable": True, "status": "confirmed", "statusDate": "2026-10-08"})
        response = self.post_checklist({
            "revision": data["revision"], "action": "confirm", "items": items,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.get_checklist()["version"], 0)

    def test_evidence_file_upload_and_download(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        settings_override = override_settings(MEDIA_ROOT=temporary.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        item = self.get_checklist()["items"][0]
        upload_url = f"{self.url}evidence/{item['pk']}/"
        response = self.client.post(
            upload_url,
            {"file": SimpleUploadedFile(
                "notice.pdf", b"%PDF-1.4 evidence", content_type="application/pdf"
            )},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200, response.data)
        uploaded = response.data["items"][0]
        self.assertEqual(uploaded["evidenceFileName"], "notice.pdf")
        download = self.client.get(uploaded["evidenceUrlForDownload"])
        self.assertEqual(download.status_code, 200)
        download.close()
