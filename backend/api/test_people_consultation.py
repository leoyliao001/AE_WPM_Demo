from copy import deepcopy
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from api.models import (
    MigrationIntakeSubmission,
    MigrationTeam,
    StakeholderRegistration,
    UserNameList,
)


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
        self.assertTrue(response.data["checklistConfirmed"])
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
        self.assertFalse(reopened.data["checklistConfirmed"])
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

    def test_confirmed_status_requires_date_and_evidence_or_outcome(self):
        data = self.get_checklist()
        items = deepcopy(data["items"])
        items[0].update({"status": "confirmed", "statusDate": "2026-10-08"})
        response = self.post_checklist({
            "revision": data["revision"], "action": "save", "items": items,
        })
        self.assertEqual(response.status_code, 400)

        items[0]["outcomeNote"] = "HR team briefed."
        response = self.post_checklist({
            "revision": data["revision"], "action": "save", "items": items,
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["items"][0]["status"], "confirmed")

    def test_assigned_migration_manager_controls_owner_updates(self):
        manager = MigrationTeam.objects.create(role="Manager", email="manager@example.com")
        StakeholderRegistration.objects.create(
            project=self.project,
            team_members=[
                {
                    "id": f"migration-team-{manager.pk}",
                    "fullName": "Project Migration Manager",
                    "email": "manager@example.com",
                },
                {"id": "member-1", "fullName": "Team Member", "email": "member@example.com"},
            ],
            assignments={
                "migration_manager": {
                    "personIds": [f"migration-team-{manager.pk}"],
                    "lockedAt": "",
                    "lockedBy": "",
                }
            },
        )
        data = self.get_checklist()
        self.assertTrue(data["canManageOwners"])
        items = deepcopy(data["items"])
        items[0]["ownerRole"] = "HR Business Partner"

        self.client.credentials(HTTP_X_USER_EMAIL="member@example.com")
        member_data = self.get_checklist()
        self.assertFalse(member_data["canManageOwners"])
        denied = self.post_checklist({
            "revision": member_data["revision"], "action": "save", "items": items,
        })
        self.assertEqual(denied.status_code, 403)

        self.client.credentials(HTTP_X_USER_EMAIL="manager@example.com")
        manager_data = self.get_checklist()
        self.assertTrue(manager_data["canManageOwners"])
        items = deepcopy(manager_data["items"])
        items[0]["ownerRole"] = "HR Business Partner"
        allowed = self.post_checklist({
            "revision": manager_data["revision"], "action": "save", "items": items,
        })
        self.assertEqual(allowed.status_code, 200, allowed.data)
        self.assertEqual(allowed.data["items"][0]["ownerRole"], "HR Business Partner")

    def test_owner_autocomplete_searches_directory_by_name_and_email(self):
        person = UserNameList.objects.create(
            display_name="Jordan Example",
            mail="jordan@example.com",
        )
        endpoint = f"{self.url}people/"

        by_name = self.client.get(endpoint, {"q": "Jordan"})
        self.assertEqual(by_name.status_code, 200, by_name.data)
        self.assertEqual(by_name.data["rows"][0]["id"], str(person.pk))

        by_email = self.client.get(endpoint, {"q": "example.com"})
        self.assertEqual(by_email.status_code, 200, by_email.data)
        self.assertEqual(by_email.data["rows"][0]["email"], "jordan@example.com")

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
