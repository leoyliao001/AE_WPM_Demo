import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from api.models import MigrationIntakeSubmission, ScopeStatement, ScopeStatementEvidence, ScopeStatementLine


class ScopePageTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        settings = override_settings(MEDIA_ROOT=self.media.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="SCOPE-PAGE-TEST", requestor="scope@example.com",
            project_name="Scope page test", fte_number="6",
        )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL="scope@example.com")
        self.url = f"/api/migration-dashboard/projects/{self.project.pk}/scope-statement/"
        self.statement = ScopeStatement.objects.create(project=self.project)
        for level in ("JL2", "JL3", "JL4"):
            ScopeStatementLine.objects.create(statement=self.statement, job_level=level)

    def payload(self, action="save"):
        return {
            "action": action, "scopeText": "Transfer support operations.",
            "migratableFte": "6", "migratableFteConfirmed": True,
            "outOfScope": "Sales", "assumptions": "Systems remain available",
            "waves": [{"name": "First wave", "date": "2027-01-01", "fte": 6}],
            "lines": [
                {"jobLevel": level, "agreedFte": 2, "notAgreedFte": 0, "finalFte": 2}
                for level in ("JL2", "JL3", "JL4")
            ],
        }

    def save(self, payload):
        return self.client.post(self.url + "save/", payload, format="json")

    def upload(self, suffix="attachments/"):
        return self.client.post(self.url + suffix, {
            "file": SimpleUploadedFile("agreement.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        }, format="multipart")

    def test_shared_upload_download_and_lock_all(self):
        response = self.upload()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data["attachments"]), 1)
        self.assertTrue(all(not line["evidence"] for line in response.data["lines"]))
        item = ScopeStatementEvidence.objects.get()
        self.assertEqual(item.statement, self.statement)
        self.assertIsNone(item.line)
        download = self.client.get(self.url + f"evidence/download/{item.pk}/")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(b"".join(download.streaming_content), b"%PDF-1.4 test")
        download.close()
        response = self.save(self.payload("lock"))
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["pageLocked"])
        self.assertTrue(all(line["lockedAt"] for line in response.data["lines"]))
        self.assertEqual(len({line["lockedAt"] for line in response.data["lines"]}), 1)

    def test_lock_requires_attachment_and_all_values_without_partial_writes(self):
        self.assertEqual(self.save(self.payload("lock")).status_code, 400)
        self.assertTrue(all(line.final_fte is None for line in self.statement.lines.all()))
        self.upload()
        payload = self.payload("lock")
        payload["lines"][2]["finalFte"] = None
        self.assertEqual(self.save(payload).status_code, 400)
        self.statement.refresh_from_db()
        self.assertEqual(self.statement.scope_text, "")
        self.assertTrue(all(line.final_fte is None for line in self.statement.lines.all()))
        payload = self.payload("lock")
        payload["waves"][0]["fte"] = 5
        self.assertEqual(self.save(payload).status_code, 400)
        self.assertFalse(self.statement.lines.filter(locked_at__isnull=False).exists())

    def test_missing_stored_file_returns_explicit_error_without_removing_record(self):
        self.upload()
        item = ScopeStatementEvidence.objects.get()
        item.file.storage.delete(item.file.name)
        response = self.client.get(self.url + f"evidence/download/{item.pk}/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("missing from storage", str(response.data["detail"]))
        self.assertTrue(ScopeStatementEvidence.objects.filter(pk=item.pk).exists())

    def test_manual_value_is_independent_and_confirmation_is_required(self):
        self.upload()
        payload = self.payload("lock")
        payload["migratableFte"] = "9.5"
        payload["migratableFteConfirmed"] = False
        response = self.save(payload)
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("confirm", response.data["error"])
        self.statement.refresh_from_db()
        self.assertIsNone(self.statement.migratable_fte)
        payload["migratableFteConfirmed"] = True
        response = self.save(payload)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["migratableFte"], "9.5000")
        self.assertTrue(response.data["migratableFteConfirmed"])
        self.assertEqual(self.save({"action": "submit"}).status_code, 200)
        from api.services.business_case import source_data
        from api.services.project_charter import build_charter_sources
        scope = source_data(self.project)[1]
        self.assertEqual(scope["migratableFte"], "9.5000")
        self.assertEqual(scope["finalProjectFte"], 6)
        self.assertTrue(scope["migratableFteConfirmed"])
        sources = build_charter_sources(self.project)[0]
        fact = next(fact for fact in sources["facts"] if fact["label"].startswith("Migratable FTE"))
        self.assertEqual(fact["value"], "9.5000")

    def test_manual_value_changes_clear_confirmation_and_jl_changes_do_not_override_it(self):
        self.assertEqual(self.save(self.payload()).status_code, 200)
        response = self.save({"migratableFte": "8.25"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["migratableFteConfirmed"])
        self.assertEqual(response.data["migratableFte"], "8.2500")
        response = self.save({"lines": [{"jobLevel": "JL2", "agreedFte": 50, "notAgreedFte": 0, "finalFte": 2}]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["migratableFte"], "8.2500")
        response = self.save({"migratableFteConfirmed": True})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["migratableFteConfirmed"])

    def test_invalid_manual_values_are_rejected_without_partial_saves(self):
        for value in (-1, True, "NaN", "Infinity", "0.00001", "100000000"):
            response = self.save({**self.payload(), "migratableFte": value})
            self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(self.save({"migratableFteConfirmed": "true"}).status_code, 400)
        self.assertEqual(self.save({"migratableFteConfirmed": True}).status_code, 400)
        self.statement.refresh_from_db()
        self.assertIsNone(self.statement.migratable_fte)
        self.assertFalse(self.statement.migratable_fte_confirmed)
        self.assertEqual(self.statement.scope_text, "")

    def test_legacy_value_is_not_silently_confirmed_or_exposed_as_manual_downstream(self):
        from api.services.business_case import source_data
        self.statement.lines.update(agreed_fte=2)
        response = self.client.get(self.url)
        self.assertIsNone(response.data["migratableFte"])
        self.assertFalse(response.data["migratableFteConfirmed"])
        self.assertNotIn("migratableFte", source_data(self.project)[1])

    def test_page_lock_blocks_narrative_fte_upload_and_admin_updates(self):
        self.upload()
        self.assertEqual(self.save(self.payload("lock")).status_code, 200)
        for payload in ({"scopeText": "Bypass"}, {"outOfScope": "Bypass"}, self.payload()):
            self.assertEqual(self.save(payload).status_code, 409)
        self.assertEqual(self.upload().status_code, 409)
        self.assertEqual(self.upload("evidence/JL3/").status_code, 409)
        self.client.credentials(HTTP_X_USER_EMAIL="local.dev@localhost")
        response = self.client.post("/api/migration-dashboard/scope-statements/data/", {
            "uniqueData": [{"statement_id": self.statement.pk, "scope_text": "Admin bypass"}],
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.statement.refresh_from_db()
        self.assertEqual(self.statement.scope_text, "Transfer support operations.")

    def test_unlock_clears_legacy_partial_locks_and_preserves_files(self):
        self.upload()
        self.statement.lines.filter(job_level="JL2").update(locked_at=timezone.now(), locked_by="legacy")
        self.assertTrue(self.client.get(self.url).data["pageLocked"])
        response = self.save({"action": "unlock"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["pageLocked"])
        self.assertFalse(self.statement.lines.filter(locked_at__isnull=False).exists())
        self.assertEqual(len(response.data["attachments"]), 1)
        self.assertEqual(self.save(self.payload()).status_code, 200)

    def test_submit_reopen_and_unlock(self):
        self.upload()
        self.assertEqual(self.save(self.payload("lock")).status_code, 200)
        self.assertEqual(self.save({"action": "submit", "scopeText": "Bypass lock"}).status_code, 409)
        response = self.save({"action": "submit"})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "submitted")
        self.assertEqual(response.data["finalProjectFte"], 6)
        self.assertEqual(self.save({"action": "unlock"}).status_code, 409)
        self.assertEqual(self.upload().status_code, 409)
        response = self.save({"action": "revise", "reason": "Update planned scope"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["pageLocked"])
        self.assertEqual(self.save({"action": "unlock"}).status_code, 200)
        self.assertEqual(self.upload().status_code, 201)

    def test_stale_revision_and_invalid_line_do_not_change_saved_values(self):
        self.upload()
        self.assertEqual(self.save({**self.payload(), "revision": 0}).status_code, 409)
        payload = self.payload()
        payload["lines"][2]["finalFte"] = -1
        self.assertEqual(self.save(payload).status_code, 400)
        self.assertTrue(all(line.final_fte is None for line in self.statement.lines.all()))
        self.assertEqual(self.client.post(self.url + "attachments/", {
            "revision": "0", "file": SimpleUploadedFile("stale.pdf", b"pdf"),
        }, format="multipart").status_code, 409)
        self.assertEqual(ScopeStatementEvidence.objects.count(), 1)

    def test_legacy_endpoint_creates_shared_attachment_and_access_is_enforced(self):
        self.assertEqual(self.upload("evidence/JL2/").status_code, 201)
        self.assertIsNone(ScopeStatementEvidence.objects.get().line_id)
        self.client.credentials(HTTP_X_USER_EMAIL="other@example.com")
        self.assertEqual(self.upload().status_code, 403)
        item = ScopeStatementEvidence.objects.get()
        self.assertEqual(self.client.get(self.url + f"evidence/download/{item.pk}/").status_code, 403)
