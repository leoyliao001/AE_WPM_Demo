from copy import deepcopy
from io import StringIO
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from api.models import (
    AccessEnablement, MigrationIntakeSubmission, ProjectAttributesAccess,
    ProjectResources, ScopeStatement, ScopeStatementLine, StakeholderRegistration,
)
from api.services.project_artefacts import IT_ITEMS


class ProjectArtefactTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="ARTEFACT-TEST", requestor="owner@example.com",
            project_name="Artefact test", fte_number="1", region="EUR", areas=["EME"],
            countries=["Egypt"], products=["General Ocean"], default_location_strategies=["Pune"],
        )
        self.scope = ScopeStatement.objects.create(
            project=self.project, scope_text="Transfer support", final_project_fte=1, status="submitted",
        )
        for level in ("JL2", "JL3", "JL4"):
            ScopeStatementLine.objects.create(
                statement=self.scope, job_level=level, final_fte=1 if level == "JL2" else 0, locked_at=timezone.now(),
            )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.base = f"/api/migration-dashboard/projects/{self.project.pk}/"
        self.registry = StakeholderRegistration.objects.create(
            project=self.project,
            team_members=[
                {"id": "gsc", "fullName": "GSC", "email": "gsc@example.com"},
                {"id": "area", "fullName": "Area", "email": "area@example.com"},
                {"id": "viewer", "fullName": "Viewer", "email": "viewer@example.com"},
            ],
            assignments={
                "gsc_leaders": {"personIds": ["gsc"], "lockedAt": "2026-10-28"},
                "area_poc": {"personIds": ["area"], "lockedAt": "2026-10-28"},
            },
        )

    def get(self, kind):
        return self.client.get(self.base + kind + "/")

    def post(self, kind, action="save", **changes):
        current = self.get(kind)
        self.assertEqual(current.status_code, 200, current.data)
        data = current.data
        payload = {
            "revision": data["revision"], "sourceVersion": data["source"]["version"],
            "action": action,
        }
        for key in ("rows", "systems", "barriers", "itItems"):
            if key in data:
                payload[key] = deepcopy(data[key])
        payload.update(changes)
        return self.client.post(self.base + kind + "/", payload, format="json")

    def resource(self, efficiency=False):
        return {
            "id": "position-1", "site": "Pune", "hiringType": "Efficiency" if efficiency else "External",
            "language": "English", "pidCreationDate": "2026-01-01", "gscPid": "GSC-001",
            "deletedPid": "DEL-1" if efficiency else "", "region": "EUR", "area": "EME", "country": "Egypt",
            "areaPid": "AREA-001", "areaApmmId": "A-001", "releaseDate": "2027-01-01",
            "requisitionId": "REQ-1", "hiringStatus": "Onboarded", "remarks": "Ready",
            "tentativeDoj": "2027-01-01", "actualDoj": "2027-01-02", "apmmId": "APMM-1",
        }

    def system(self, secured=True):
        return {"id": "system-1", "systemId": "salesforce", "accessType": "Ocean profile", "usersNeeded": 1, "isSecured": secured}

    def barrier(self):
        return {"id": "barrier-1", "systemLineId": "system-1", "type": "Licensing",
                "owner": "it@example.com", "targetDate": "2020-01-01", "description": "Licence required"}

    def ready_access(self):
        response = self.post("access-enablement", systems=[self.system()])
        self.assertEqual(response.status_code, 200, response.data)
        self.client.credentials(HTTP_X_USER_EMAIL="gsc@example.com")
        response = self.post("access-enablement", "confirm_it",
                             itItems=[{"id": item["id"], "qtyConfirmed": 1} for item in IT_ITEMS],
                             confirmationComment="All equipment ready")
        self.assertEqual(response.status_code, 200, response.data)
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        return response

    def test_get_is_read_only_and_population_is_final_fte_not_migratable(self):
        self.scope.migratable_fte = 9
        self.scope.migratable_fte_confirmed = True
        self.scope.save()
        for kind in ("resources", "access-enablement"):
            data = self.get(kind).data
            self.assertEqual(data["source"]["population"], 1)
            self.assertFalse(data["saved"])
        self.assertFalse(ProjectResources.objects.exists())
        self.assertFalse(AccessEnablement.objects.exists())

    def test_acl_unsigned_outsider_viewer_and_permissions(self):
        self.client.credentials()
        self.assertEqual(self.get("resources").status_code, 401)
        self.client.credentials(HTTP_X_USER_EMAIL="outsider@example.com")
        self.assertEqual(self.get("resources").status_code, 403)
        self.client.credentials(HTTP_X_USER_EMAIL="viewer@example.com")
        self.assertEqual(self.get("resources").status_code, 200)
        self.assertEqual(self.post("resources", rows=[]).status_code, 403)
        self.assertEqual(self.post("access-enablement").status_code, 403)
        ProjectAttributesAccess.objects.create(email="admin@example.com", resources=True, access_enablement=True)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@example.com")
        self.assertTrue(self.get("access-enablement").data["permissions"]["it"])
        self.assertEqual(self.post("resources", rows=[]).status_code, 200)

    def test_resource_hiring_flow_confirm_freeze_reopen_and_history(self):
        self.assertEqual(self.post("resources", rows=[self.resource()]).status_code, 200)
        response = self.post("resources", "submit_area")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["rows"][0]["areaLockedAt"])
        self.assertTrue(response.data["ready"])
        response = self.post("resources", "submit")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "confirmed")
        self.assertEqual(self.post("resources").status_code, 409)
        self.assertEqual(self.post("resources", "reopen", reason="").status_code, 400)
        response = self.post("resources", "reopen", reason="Change plan")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["frozen"])
        self.assertEqual(response.data["auditLog"][-1]["reason"], "Change plan")

    def test_area_permissions_and_lock_cannot_be_bypassed(self):
        self.assertEqual(self.post("resources", rows=[self.resource()]).status_code, 200)
        self.client.credentials(HTTP_X_USER_EMAIL="area@example.com")
        response = self.post("resources", "submit_area")
        self.assertEqual(response.status_code, 200, response.data)
        row = response.data["rows"][0]
        self.assertEqual(self.post("resources", rows=[{**row, "areaPid": "bypass"}]).status_code, 400)
        self.assertEqual(self.post("resources", rows=[{**row, "gscPid": "bypass"}]).status_code, 403)
        self.assertEqual(self.post("resources", rows=[]).status_code, 403)
        response = self.post("resources", "reopen_area", reason="Correct area")
        self.assertEqual(response.status_code, 200)
        row = response.data["rows"][0]
        self.assertEqual(self.post("resources", rows=[{**row, "areaPid": "corrected"}]).status_code, 200)

    def test_efficiency_does_not_require_recruitment_and_preserves_actual_doj(self):
        response = self.post("resources", rows=[self.resource(True)])
        self.assertEqual(response.status_code, 200)
        row = response.data["rows"][0]
        self.assertEqual(row["hiringStatus"], "Not Applicable")
        self.assertEqual(row["requisitionId"], "")
        self.assertEqual(row["tentativeDoj"], "")
        self.assertEqual(row["actualDoj"], "2027-01-02")
        self.assertEqual(self.post("resources", "submit_area").status_code, 200)
        self.assertEqual(self.post("resources", "submit").status_code, 200)

    def test_resource_validation_is_atomic_and_scope_required(self):
        self.assertEqual(self.post("resources", rows=[self.resource()]).status_code, 200)
        for row in ({**self.resource(), "actualDoj": "bad"}, {**self.resource(), "hiringType": "invalid"},
                    {**self.resource(), "hiringStatus": "Onboarded", "apmmId": ""}):
            self.assertEqual(self.post("resources", rows=[row]).status_code, 400)
        self.assertEqual(ProjectResources.objects.get().revision, 1)
        self.scope.status = "draft"
        self.scope.save()
        self.assertIsNone(self.get("resources").data["source"]["population"])
        self.assertEqual(self.post("resources", "submit").status_code, 400)

    def test_access_barrier_required_validation_and_resolution_history(self):
        self.assertEqual(self.post("access-enablement", systems=[self.system(False)]).status_code, 400)
        self.assertFalse(AccessEnablement.objects.exists())
        for change in ({"owner": "not-email"}, {"targetDate": "bad"}, {"description": "x" * 501}):
            self.assertEqual(self.post("access-enablement", systems=[self.system(False)], barriers=[{**self.barrier(), **change}]).status_code, 400)
        response = self.post("access-enablement", systems=[self.system(False)], barriers=[self.barrier()])
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["summary"]["overdueBarriers"], 1)
        self.assertEqual(response.data["status"], "at_risk")
        self.assertEqual(self.post("access-enablement", barriers=[]).status_code, 400)
        response = self.post("access-enablement", systems=[self.system()])
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["barriers"][0]["status"], "resolved")
        self.assertTrue(response.data["barriers"][0]["resolvedAt"])
        self.assertEqual(response.data["summary"]["openBarriers"], 0)
        barrier = response.data["barriers"][0]
        self.assertEqual(self.post("access-enablement", barriers=[{**barrier, "description": "tamper"}]).status_code, 400)

    def test_it_role_separation_ready_submit_and_freeze(self):
        self.assertEqual(self.post("access-enablement", "confirm_it").status_code, 403)
        response = self.ready_access()
        self.assertTrue(response.data["summary"]["ready"])
        self.assertEqual(response.data["itConfirmation"]["by"], "gsc@example.com")
        self.assertEqual(response.data["itItems"][0]["updatedBy"], "gsc@example.com")
        response = self.post("access-enablement", "submit")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["frozen"])
        self.assertEqual(self.post("access-enablement").status_code, 409)
        response = self.post("access-enablement", "reopen", reason="Update equipment")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["itConfirmation"], {})

    def test_it_quantity_edit_reopens_confirmation(self):
        self.ready_access()
        self.client.credentials(HTTP_X_USER_EMAIL="gsc@example.com")
        items = [{"id": item["id"], "qtyConfirmed": 1} for item in IT_ITEMS]
        items[0]["qtyConfirmed"] = 0
        response = self.post("access-enablement", itItems=items)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data["summary"]["itConfirmed"])
        self.assertFalse(response.data["summary"]["ready"])
        self.assertEqual(response.data["itConfirmation"], {})
        self.assertEqual(self.post("access-enablement", "confirm_it").status_code, 400)
        self.assertEqual(self.post("access-enablement", systems=[self.system(False)], barriers=[self.barrier()]).status_code, 403)

    def test_source_change_invalidates_confirmation_and_secured_status(self):
        self.ready_access()
        self.assertEqual(self.post("access-enablement", "submit").status_code, 200)
        self.scope.revision += 1
        self.scope.save()
        data = self.get("access-enablement").data
        self.assertEqual(data["status"], "needs_review")
        self.assertFalse(data["summary"]["itConfirmed"])
        self.assertTrue(data["frozen"])
        self.assertEqual(self.post("access-enablement", "reopen", reason="Review new Scope").status_code, 200)

    def test_stale_revision_and_scope_versions_are_rejected(self):
        for kind in ("resources", "access-enablement"):
            data = self.get(kind).data
            response = self.client.post(self.base + kind + "/", {
                "revision": 99, "sourceVersion": data["source"]["version"],
            }, format="json")
            self.assertEqual(response.status_code, 409)
            response = self.client.post(self.base + kind + "/", {"revision": 0, "sourceVersion": "stale"}, format="json")
            self.assertEqual(response.status_code, 409)
        self.assertFalse(ProjectResources.objects.exists())
        self.assertFalse(AccessEnablement.objects.exists())

    def test_catalogue_and_quantities_are_validated(self):
        for system in ({**self.system(), "systemId": "not-catalogue"}, {**self.system(), "usersNeeded": True},
                       {**self.system(), "isSecured": "yes"}):
            self.assertEqual(self.post("access-enablement", systems=[system]).status_code, 400)
        self.client.credentials(HTTP_X_USER_EMAIL="local.dev@localhost")
        self.assertEqual(self.post("access-enablement", itItems=[{"id": item["id"], "qtyConfirmed": 2} for item in IT_ITEMS]).status_code, 400)

    def test_landing_only_shows_accessible_projects_and_never_uses_sample_capacity(self):
        response = self.client.get("/api/migration-dashboard/resources/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["rows"][0]["pipelineFte"], 1)
        self.scope.status = "draft"
        self.scope.save()
        response = self.client.get("/api/migration-dashboard/resources/")
        self.assertIsNone(response.data["rows"][0]["pipelineFte"])
        self.client.credentials(HTTP_X_USER_EMAIL="outsider@example.com")
        self.assertEqual(self.client.get("/api/migration-dashboard/resources/").data["count"], 0)

    def test_resource_landing_batches_non_approved_project_queries(self):
        for index in range(20):
            MigrationIntakeSubmission.objects.create(
                migration_request_id=f"PORTFOLIO-{index}", requestor="owner@example.com", project_name=f"Project {index}",
            )
        with self.assertNumQueries(6):
            response = self.client.get("/api/migration-dashboard/resources/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 21)

    def test_population_zero_can_be_explicitly_confirmed_without_fake_resource_rows(self):
        self.scope.final_project_fte = 0
        self.scope.save()
        self.scope.lines.update(final_fte=0)
        response = self.post("resources", "submit", rows=[])
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "confirmed")
        self.assertEqual(response.data["rows"], [])

    def test_resources_scope_change_invalidates_secured_status(self):
        self.assertEqual(self.post("resources", rows=[self.resource()]).status_code, 200)
        self.assertEqual(self.post("resources", "submit_area").status_code, 200)
        self.assertEqual(self.post("resources", "submit").status_code, 200)
        self.scope.review_required = True
        self.scope.save()
        data = self.get("resources").data
        self.assertEqual(data["status"], "needs_review")
        self.assertTrue(data["frozen"])
        self.assertIsNone(data["source"]["population"])

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_overdue_reminders_are_real_emails_and_deduplicated_daily(self):
        self.assertEqual(self.post("access-enablement", systems=[self.system(False)], barriers=[self.barrier()]).status_code, 200)
        call_command("notify_enablement_barriers", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["it@example.com"])
        record = AccessEnablement.objects.get()
        self.assertTrue(record.barriers[0]["lastNotifiedAt"])
        self.assertEqual(record.audit_log[-1]["action"], "overdue_notification")
        call_command("notify_enablement_barriers", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)

    def test_notification_failure_is_explicit_and_does_not_repeat_prior_success(self):
        response = self.post(
            "access-enablement",
            systems=[self.system(False), {**self.system(False), "id": "system-2", "systemId": "sap"}],
            barriers=[self.barrier(), {**self.barrier(), "id": "barrier-2", "systemLineId": "system-2"}],
        )
        self.assertEqual(response.status_code, 200, response.data)
        with patch("api.management.commands.notify_enablement_barriers.send_mail", side_effect=[1, OSError("SMTP unavailable")]):
            with self.assertLogs("api.management.commands.notify_enablement_barriers", level="ERROR"):
                with self.assertRaises(CommandError):
                    call_command("notify_enablement_barriers", stdout=StringIO())
        record = AccessEnablement.objects.get()
        self.assertTrue(record.barriers[0]["lastNotifiedAt"])
        self.assertFalse(record.barriers[1]["lastNotifiedAt"])
        with patch("api.management.commands.notify_enablement_barriers.send_mail", return_value=1) as send:
            call_command("notify_enablement_barriers", stdout=StringIO())
            self.assertEqual(send.call_count, 1)
