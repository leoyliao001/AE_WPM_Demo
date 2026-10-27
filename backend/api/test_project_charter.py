from datetime import datetime, timezone as datetime_timezone

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from api.models import (
    ApprovalWorkflow,
    MigrationIntakeSubmission,
    ProjectAttributesAccess,
    ProjectCharter,
    ProjectGanttPlan,
    ScopeStatement,
    ScopeStatementLine,
    StakeholderRegistration,
)


class ProjectCharterTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="CHARTER_TEST",
            requested_date="27 Oct 2026",
            requestor="owner@example.com",
            project_name="Charter test",
            migration_type="1:1 migration",
            migration_type_value="one_to_one",
            region="EUR",
            function_name="Ocean",
            proposed_scope="Transfer documentation",
            fte_number="12",
        )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.url = f"/api/migration-dashboard/projects/{self.project.id}/project-charter/"

    def save(self, **overrides):
        payload = {
            "revision": 0, "vision": "Charter-owned wording",
            "deliverableNotes": {"initiating": "Review with sponsor"},
            "extraSuccessCriteria": ["No disruption"],
        }
        payload.update(overrides)
        return self.client.post(self.url + "save/", payload, format="json")

    def test_get_is_read_only_and_marks_missing_sources(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["saved"])
        self.assertEqual(ProjectCharter.objects.count(), 0)
        self.assertIsNone(response.data["sources"]["facts"][3]["value"])
        self.assertIsNone(response.data["sources"]["facts"][5]["value"])
        self.assertEqual(response.data["sources"]["fteTimeline"], [])
        self.assertEqual(len(response.data["sources"]["deliverables"]), 5)
        self.assertTrue(all(not item["complete"] for item in response.data["sources"]["completeness"]))

    def test_save_reload_and_audit(self):
        response = self.save()
        self.assertEqual(response.status_code, 200)
        data = self.client.get(self.url).data
        self.assertEqual(data["vision"], "Charter-owned wording")
        self.assertEqual(data["deliverableNotes"], {"initiating": "Review with sponsor"})
        self.assertEqual(data["extraSuccessCriteria"], ["No disruption"])
        self.assertEqual(data["revision"], 1)
        self.assertEqual(data["auditLog"][0]["by"], "owner@example.com")
        self.assertFalse(data["sourceUpdated"])
        self.assertEqual(self.project.project_charter.pk, ProjectCharter.objects.get().pk)

    def test_source_data_is_live_but_does_not_replace_vision(self):
        self.save()
        self.project.project_name = "Changed upstream"
        self.project.save()
        scope = ScopeStatement.objects.create(
            project=self.project, scope_text="Live scope", status="submitted", final_project_fte=12
        )
        for level in ("JL2", "JL3", "JL4"):
            ScopeStatementLine.objects.create(statement=scope, job_level=level, final_fte=4, locked_at=timezone.now())
        data = self.client.get(self.url).data
        self.assertTrue(data["sourceUpdated"])
        self.assertEqual(data["vision"], "Charter-owned wording")
        self.assertEqual(data["sources"]["scope"]["inScope"], "Live scope")
        self.assertEqual(data["sources"]["facts"][3]["value"], 12)
        self.assertIn("12 FTE", data["sources"]["autoCriteria"][0])

    def test_regeneration_is_explicit_and_preserves_owned_notes(self):
        self.save()
        self.project.proposed_scope = "Updated scope"
        self.project.save()
        response = self.save(action="regenerate", revision=1)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Updated scope", response.data["vision"])
        self.assertEqual(response.data["deliverableNotes"]["initiating"], "Review with sponsor")
        self.assertEqual(response.data["extraSuccessCriteria"], ["No disruption"])
        self.assertEqual(response.data["revision"], 2)

    def test_stale_writes_and_delete_are_rejected(self):
        self.save()
        self.assertEqual(self.save().status_code, 409)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@localhost")
        response = self.client.post(self.url + "delete/", {"revision": 0}, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(ProjectCharter.objects.get().revision, 1)

    def test_only_owned_fields_are_written(self):
        response = self.save(status="approved", sources={"scope": {"inScope": "Forged"}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "draft")
        self.assertNotEqual(response.data["sources"]["scope"]["inScope"], "Forged")
        self.assertFalse(ScopeStatement.objects.exists())

    def test_criteria_are_add_only(self):
        self.save()
        self.assertEqual(self.save(revision=1, extraSuccessCriteria=[]).status_code, 400)
        self.assertEqual(self.save(revision=1, extraSuccessCriteria=["Changed"]).status_code, 400)
        response = self.save(revision=1, extraSuccessCriteria=["No disruption", "Review weekly"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["extraSuccessCriteria"]), 2)

    def test_invalid_inputs_do_not_create_records(self):
        for overrides in (
            {"vision": 4}, {"vision": "a" * 10001}, {"deliverableNotes": []},
            {"deliverableNotes": {"invalid": "x"}}, {"extraSuccessCriteria": [""]},
            {"extraSuccessCriteria": ["x", "x"]}, {"action": "submit"}, {"action": []},
        ):
            with self.subTest(overrides=overrides):
                self.assertEqual(self.save(**overrides).status_code, 400)
                self.assertFalse(ProjectCharter.objects.exists())

    def test_non_object_request_bodies_return_validation_errors(self):
        self.assertEqual(self.client.post(self.url + "save/", [], format="json").status_code, 400)
        self.save()
        self.client.credentials(HTTP_X_USER_EMAIL="admin@localhost")
        self.assertEqual(self.client.post(self.url + "delete/", [], format="json").status_code, 400)
        self.assertTrue(ProjectCharter.objects.exists())

    def test_exact_input_length_and_count_limits(self):
        response = self.save(
            vision="v" * 10000, deliverableNotes={"initiating": "n" * 2000},
            extraSuccessCriteria=["c" * 1000] + [f"Criterion {index}" for index in range(49)],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["vision"]), 10000)
        for overrides in (
            {"vision": "v" * 10001},
            {"deliverableNotes": {"initiating": "n" * 2001}},
            {"extraSuccessCriteria": ["c" * 1001]},
            {"extraSuccessCriteria": [f"Criterion {index}" for index in range(51)]},
        ):
            with self.subTest(field=next(iter(overrides))):
                self.assertEqual(self.save(revision=1, **overrides).status_code, 400)
                self.assertEqual(ProjectCharter.objects.get().revision, 1)

    def test_permissions_for_project_and_database(self):
        self.client.credentials()
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.credentials(HTTP_X_USER_EMAIL="stranger@example.com")
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.save().status_code, 403)
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.assertEqual(self.client.get("/api/migration-dashboard/project-charters/").status_code, 403)
        self.assertEqual(self.client.post(self.url + "delete/", {}, format="json").status_code, 403)
        ProjectAttributesAccess.objects.create(email="maintainer@example.com", project_charter=True)
        self.client.credentials(HTTP_X_USER_EMAIL="maintainer@example.com")
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.save().status_code, 200)
        listing = self.client.get("/api/migration-dashboard/project-charters/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["rows"][0]["projectId"], self.project.id)
        self.assertTrue(self.client.get("/api/project-attributes-access/me/").data["tables"]["project_charter"])

    def test_admin_delete_keeps_sources(self):
        self.save()
        ScopeStatement.objects.create(project=self.project, scope_text="Keep this")
        self.client.credentials(HTTP_X_USER_EMAIL="admin@localhost")
        response = self.client.post(self.url + "delete/", {"revision": 1}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ProjectCharter.objects.exists())
        self.assertTrue(MigrationIntakeSubmission.objects.filter(pk=self.project.id).exists())
        self.assertEqual(ScopeStatement.objects.get().scope_text, "Keep this")

    def test_locked_roles_and_business_approval_gate(self):
        now = timezone.now()
        scope = ScopeStatement.objects.create(project=self.project, status="submitted", final_project_fte=0)
        for level in ("JL2", "JL3", "JL4"):
            ScopeStatementLine.objects.create(statement=scope, job_level=level, final_fte=0, locked_at=now)
        roles = ("project_sponsor", "elt", "area_functional_leader", "gsc_head_1")
        StakeholderRegistration.objects.create(
            project=self.project,
            team_members=[{"id": "p1", "fullName": "Sponsor", "email": "sponsor@example.com"}],
            assignments={role: {"personIds": ["p1"], "lockedAt": now.isoformat()} for role in roles},
        )
        self.project.business_case_submission_date = now
        self.project.save()
        ApprovalWorkflow.objects.create(
            migration_request_id=self.project.migration_request_id,
            area_head_status="approved", pmo_status="approved", bpm_status="approved",
            wpm_review_status="approved", elt_status="approved", gsc_head_status="approved",
        )
        data = self.client.get(self.url).data
        self.assertTrue(all(item["complete"] for item in data["sources"]["completeness"]))
        self.assertEqual(data["sources"]["facts"][3]["value"], 0)
        self.assertEqual(data["sources"]["leadership"][0]["people"][0]["name"], "Sponsor")

    def test_gantt_dates_and_partial_progress_are_real(self):
        ProjectGanttPlan.objects.create(project=self.project, tasks=[
            {"id": "neo-training", "name": "Training", "plan": {"startWeek": 1, "endWeek": 2}, "completedAt": timezone.now().isoformat()},
        ])
        data = self.client.get(self.url).data
        executing = next(row for row in data["sources"]["deliverables"] if row["id"] == "executing")
        self.assertEqual(executing["status"], "in_progress")
        self.assertTrue(executing["timeline"])
        self.assertFalse(any(row["status"] == "complete" for row in data["sources"]["deliverables"]))

    @override_settings(TIME_ZONE="Asia/Shanghai")
    def test_gantt_dates_follow_the_same_local_week_as_the_source(self):
        MigrationIntakeSubmission.objects.filter(pk=self.project.pk).update(
            created_at=datetime(2026, 1, 4, 23, tzinfo=datetime_timezone.utc)
        )
        ProjectGanttPlan.objects.create(project=self.project, tasks=[
            {"id": "neo-training", "name": "Training", "plan": {"startWeek": 1, "endWeek": 2}},
        ])
        data = self.client.get(self.url).data
        self.assertEqual(data["sources"]["facts"][4]["value"], "2026-01-12 - 2026-01-25")

    def test_empty_saved_gantt_does_not_invent_dates(self):
        ProjectGanttPlan.objects.create(project=self.project, tasks=[])
        data = self.client.get(self.url).data
        self.assertEqual(data["sources"]["facts"][4]["value"], "")
        self.assertTrue(all(not row["timeline"] for row in data["sources"]["deliverables"]))

    def test_saved_draft_is_not_a_completed_dashboard_artefact(self):
        self.save()
        data = self.client.get(f"/api/migration-dashboard/projects/{self.project.id}/").data
        self.assertTrue(data["projectCharterSaved"])

    def test_missing_project(self):
        self.assertEqual(self.client.get("/api/migration-dashboard/projects/999999/project-charter/").status_code, 404)
