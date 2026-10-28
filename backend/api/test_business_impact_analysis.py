from copy import deepcopy

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from api.models import (
    BusinessImpactAnalysis, MigrationIntakeSubmission, OpportunityAssessment,
    ProjectAttributesAccess, ScopeStatement, ScopeStatementLine, StakeholderRegistration,
)


class BusinessImpactAnalysisTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="BIA-TEST", project_name="BCP migration", requestor="owner@example.com",
            function_name="Order to cash", products=["Ocean"], region="EUR", areas=["NEU"],
            default_location_strategies=["Pune"], fte_number="12",
        )
        self.scope = ScopeStatement.objects.create(
            project=self.project, scope_text="Invoice processing", status="submitted", final_project_fte=12,
            migratable_fte=99, migratable_fte_confirmed=True,
        )
        for level in ("JL2", "JL3", "JL4"):
            ScopeStatementLine.objects.create(
                statement=self.scope, job_level=level, final_fte=12 if level == "JL2" else 0,
                locked_at=timezone.now(),
            )
        self.registry = StakeholderRegistration.objects.create(
            project=self.project,
            team_members=[
                {"id": role, "fullName": role.title(), "email": f"{role}@example.com"}
                for role in ("migration", "area", "execution", "resilience", "viewer")
            ],
            assignments={
                code: {"personIds": [role], "lockedAt": "2026-10-28"}
                for code, role in [("wpm_focals", "migration"), ("area_sme", "area"),
                                   ("gsc_leaders", "execution"), ("business_resilience", "resilience")]
            },
        )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.url = f"/api/migration-dashboard/projects/{self.project.pk}/business-impact-analysis/"

    def get(self):
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200, result.data)
        return result.data

    def complete(self, questionnaire):
        questionnaire = deepcopy(questionnaire)
        questionnaire["answers"] = {
            "processType": "new", "sla": "24 hours", "peakDays": "1-3",
            "peakMonths": "December", "languageFte": "None", "startUtc": "22:00", "endUtc": "06:00",
            "operatingDays": ["Monday", "Tuesday"], "applications": ["SAP"], "secondSite": "no",
            "retainSupport": "no", "otherInformation": "None",
        }
        return questionnaire

    def post(self, action="save", questionnaire=None, index=0, **extra):
        data = self.get()
        q = deepcopy(questionnaire or data["questionnaires"][index])
        return self.client.post(self.url, {
            "revision": data["revision"], "sourceVersion": data["source"]["version"],
            "action": action, "processId": q["id"], "questionnaire": q, **extra,
        }, format="json")

    def submitted(self):
        q = self.complete(self.get()["questionnaires"][0])
        response = self.post("submit", q)
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def reviews(self):
        for role in ("migration", "area", "execution", "resilience"):
            self.client.credentials(HTTP_X_USER_EMAIL=f"{role}@example.com")
            response = self.post("review", reviewRole=role, comment=f"{role} checked")
            self.assertEqual(response.status_code, 200, response.data)
        return response

    def test_get_readonly_prefills_locked_final_fte_and_fallback(self):
        data = self.get()
        self.assertFalse(data["saved"])
        self.assertFalse(BusinessImpactAnalysis.objects.exists())
        self.assertEqual(data["source"]["population"], 12)
        self.assertEqual(data["source"]["subprocesses"], "Invoice processing")
        self.assertEqual(data["questionnaires"][0]["id"], "intake-scope")
        self.assertEqual(data["questionnaires"][0]["process"]["name"], "Order to cash")
        self.assertEqual(data["source"]["reviewers"]["area"][0]["email"], "area@example.com")

    def test_acl_unsigned_outsider_viewer_area_and_admin(self):
        self.client.credentials()
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.credentials(HTTP_X_USER_EMAIL="outsider@example.com")
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.credentials(HTTP_X_USER_EMAIL="viewer@example.com")
        self.assertEqual(self.post().status_code, 403)
        self.client.credentials(HTTP_X_USER_EMAIL="area@example.com")
        self.assertEqual(self.post().status_code, 200)
        ProjectAttributesAccess.objects.create(email="admin@example.com", business_impact_analysis=True)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@example.com")
        self.assertTrue(self.get()["permissions"]["admin"])
        self.assertEqual(self.post().status_code, 200)

    def test_complete_workflow_freeze_role_identity_and_signoff(self):
        data = self.submitted()
        self.assertEqual(data["questionnaires"][0]["progress"]["answered"], 10)
        self.assertEqual(data["questionnaires"][0]["status"], "submitted")
        self.assertEqual(self.post().status_code, 409)
        self.assertEqual(self.post("review", reviewRole="area").status_code, 403)
        self.assertEqual(self.post("sign_off").status_code, 403)
        self.client.credentials(HTTP_X_USER_EMAIL="area@example.com")
        self.assertEqual(self.post("sign_off").status_code, 400)
        self.reviews()
        self.client.credentials(HTTP_X_USER_EMAIL="execution@example.com")
        response = self.post("sign_off")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "confirmed")
        self.assertTrue(response.data["ready"])
        self.assertEqual(response.data["questionnaires"][0]["signedOffBy"], "execution@example.com")
        self.assertEqual(self.post().status_code, 403)
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.assertEqual(self.post("reopen", reason="").status_code, 400)
        reopened = self.post("reopen", reason="Update service window")
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(reopened.data["questionnaires"][0]["reviews"], {})
        self.assertEqual(reopened.data["questionnaires"][0]["status"], "draft")
        self.assertEqual(reopened.data["auditLog"][-1]["reason"], "Update service window")
        self.assertEqual(len(reopened.data["auditLog"][-1]["old"]["questionnaires"]["intake-scope"]["reviews"]), 4)

    def test_exact_ten_answers_and_draft_without_ready_scope(self):
        q = self.complete(self.get()["questionnaires"][0])
        q["answers"]["otherInformation"] = ""
        response = self.post("save", q)
        self.assertEqual(response.data["questionnaires"][0]["progress"]["answered"], 9)
        self.assertEqual(self.post("submit", q).status_code, 400)
        q["answers"]["otherInformation"] = "None"
        self.scope.status = "draft"
        self.scope.save()
        response = self.post("save", q)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["source"]["population"])
        self.assertIn("Q4", response.data["questionnaires"][0]["progress"]["blockers"])
        self.assertEqual(self.post("submit", q).status_code, 400)

    def test_second_site_flag_and_mitigation_owners_dates_required(self):
        q = self.complete(self.get()["questionnaires"][0])
        q["answers"]["secondSite"] = "maybe"
        saved = self.post("save", q)
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.data["questionnaires"][0]["flags"], [{"id": "second_site", "owner": "", "dueDate": ""}])
        self.assertEqual(self.post("submit").status_code, 400)
        q = saved.data["questionnaires"][0]
        q["flags"][0].update({"owner": "risk@example.com", "dueDate": "2027-01-01"})
        self.assertEqual(self.post("submit", q).status_code, 400)
        q["mitigations"] = [{"id": "a1", "description": "Evaluate backup site", "owner": "risk@example.com",
                             "dueDate": "2027-01-01", "status": "open"}]
        self.assertEqual(self.post("submit", q).status_code, 200)

    def test_invalid_inputs_are_explicit_and_do_not_persist(self):
        q = self.complete(self.get()["questionnaires"][0])
        for key, value in [("processType", "bogus"), ("secondSite", True), ("startUtc", "25:00"),
                           ("operatingDays", ["Monday", "Monday"]), ("applications", ["SAP", "sap"]),
                           ("applications", [42]), ("retainSupport", "maybe")]:
            invalid = deepcopy(q)
            invalid["answers"][key] = value
            with self.subTest(key=key, value=value):
                self.assertEqual(self.post(questionnaire=invalid).status_code, 400)
        invalid = deepcopy(q)
        invalid["flags"] = [{"id": "critical", "owner": "not-email", "dueDate": "2027-01-01"}]
        self.assertEqual(self.post(questionnaire=invalid).status_code, 400)
        invalid["flags"][0]["owner"] = "owner@example.com"
        invalid["flags"][0]["dueDate"] = "2027-02-30"
        self.assertEqual(self.post(questionnaire=invalid).status_code, 400)
        invalid["flags"] = [{"id": "made-up", "owner": "", "dueDate": ""}]
        self.assertEqual(self.post(questionnaire=invalid).status_code, 400)
        self.assertFalse(BusinessImpactAnalysis.objects.exists())

    def test_new_process_clears_current_gsc_no_contingency_clears_details_and_no_client_reviews(self):
        q = self.complete(self.get()["questionnaires"][0])
        q["answers"].update({"currentGsc": "Old site", "retainedDetails": "stale"})
        q.update({"status": "signed_off", "reviews": {"area": {"by": "fake@example.com"}}})
        response = self.post(questionnaire=q)
        self.assertEqual(response.status_code, 200)
        saved = response.data["questionnaires"][0]
        self.assertEqual(saved["status"], "draft")
        self.assertEqual(saved["reviews"], {})
        self.assertEqual(saved["answers"]["currentGsc"], "")
        self.assertEqual(saved["answers"]["retainedDetails"], "")

    def test_existing_process_requires_current_gsc_and_retained_support_details(self):
        q = self.complete(self.get()["questionnaires"][0])
        q["answers"].update({"processType": "existing", "retainSupport": "yes"})
        response = self.post(questionnaire=q)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Q7", response.data["questionnaires"][0]["progress"]["blockers"])
        self.assertIn("Q9", response.data["questionnaires"][0]["progress"]["blockers"])
        q["answers"].update({"currentGsc": "Chengdu", "retainedDetails": "1 JL3 FTE for 3 months"})
        self.assertEqual(self.post("submit", q).status_code, 200)

    def test_stale_revision_and_source_conflicts_preserve_data(self):
        data = self.get()
        self.assertEqual(self.post().status_code, 200)
        payload = {"revision": data["revision"], "sourceVersion": data["source"]["version"],
                   "processId": "intake-scope", "questionnaire": data["questionnaires"][0]}
        self.assertEqual(self.client.post(self.url, payload, format="json").status_code, 409)
        current = self.get()
        self.project.default_location_strategies = ["Chengdu"]
        self.project.save()
        payload["revision"] = current["revision"]
        self.assertEqual(self.client.post(self.url, payload, format="json").status_code, 409)
        self.assertEqual(BusinessImpactAnalysis.objects.get().revision, 1)

    def test_source_prefills_update_invalidate_reviews_and_log_old_new(self):
        self.submitted()
        self.reviews()
        self.client.credentials(HTTP_X_USER_EMAIL="execution@example.com")
        self.assertEqual(self.post("sign_off").status_code, 200)
        self.project.default_location_strategies = ["Chengdu"]
        self.project.save()
        data = self.get()
        self.assertEqual(data["status"], "needs_review")
        self.assertFalse(data["ready"])
        self.assertEqual(data["source"]["sites"], ["Chengdu"])
        self.assertEqual(data["questionnaires"][0]["reviews"], {})
        self.assertEqual(self.post("review", reviewRole="execution").status_code, 400)
        self.client.credentials(HTTP_X_USER_EMAIL="area@example.com")
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["questionnaires"][0]["status"], "draft")
        entry = response.data["auditLog"][-1]
        self.assertEqual(entry["old"]["source"]["sites"], ["Pune"])
        self.assertEqual(entry["new"]["source"]["sites"], ["Chengdu"])

    def test_unlocked_reviewer_cannot_review_and_admin_cannot_invent_missing_role(self):
        self.submitted()
        ProjectAttributesAccess.objects.create(email="admin@example.com", business_impact_analysis=True)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@example.com")
        response = self.post("review", reviewRole="area")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["questionnaires"][0]["reviews"]["area"]["adminOverride"])
        self.assertEqual(self.post("review", reviewRole="area").status_code, 400)
        self.registry.assignments["business_resilience"]["lockedAt"] = ""
        self.registry.save()
        self.assertEqual(self.post("review", reviewRole="resilience").status_code, 400)
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.assertEqual(self.post("submit").status_code, 200)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@example.com")
        self.assertEqual(self.post("review", reviewRole="resilience").status_code, 400)

    def test_relocking_same_reviewer_invalidates_previous_reviews(self):
        self.submitted()
        self.client.credentials(HTTP_X_USER_EMAIL="area@example.com")
        self.assertEqual(self.post("review", reviewRole="area").status_code, 200)
        self.registry.assignments["area_sme"]["lockedAt"] = "2026-10-29"
        self.registry.save()
        data = self.get()
        self.assertTrue(data["sourceChanged"])
        self.assertEqual(data["questionnaires"][0]["status"], "needs_review")
        self.assertEqual(data["questionnaires"][0]["reviews"], {})

    def test_multiple_processes_group_dedupe_and_removed_history(self):
        for l2, name, activity in [("Finance", "Invoicing", "Create"), ("Finance", "Invoicing", "Validate"),
                                   ("Support", "Invoicing", "Resolve")]:
            OpportunityAssessment.objects.create(
                migration_request_id=self.project.migration_request_id, l1="Ocean", l2=l2, l3=name, l4=activity,
            )
        data = self.get()
        self.assertEqual(len(data["questionnaires"]), 2)
        self.assertEqual(data["questionnaires"][0]["process"]["activities"], ["Create", "Validate"])
        ids = [q["id"] for q in data["questionnaires"]]
        for index in range(2):
            self.assertEqual(self.post("submit", self.complete(self.get()["questionnaires"][index])).status_code, 200)
        self.reviews()
        self.client.credentials(HTTP_X_USER_EMAIL="execution@example.com")
        self.assertEqual(self.post("sign_off").status_code, 200)
        self.assertFalse(self.get()["ready"])
        self.scope.scope_text = "Updated scope"
        self.scope.revision += 1
        self.scope.save()
        self.client.credentials(HTTP_X_USER_EMAIL="area@example.com")
        self.assertEqual(self.post(index=1).status_code, 200)
        record = BusinessImpactAnalysis.objects.get()
        self.assertEqual(record.questionnaires[ids[0]]["status"], "needs_review")
        self.assertEqual(record.questionnaires[ids[0]]["reviews"], {})
        OpportunityAssessment.objects.filter(l2="Finance").delete()
        data = self.get()
        self.assertEqual(len(data["questionnaires"]), 1)
        self.assertEqual(data["archivedCount"], 1)
        self.assertEqual(data["questionnaires"][0]["id"], ids[1])
        self.assertEqual(self.post().status_code, 200)
        self.assertIn(ids[0], BusinessImpactAnalysis.objects.get().questionnaires)

    def test_malformed_payload_and_unknown_action_do_not_crash(self):
        self.assertEqual(self.client.post(self.url, [], format="json").status_code, 400)
        for action in ([], "unsupported"):
            self.assertEqual(self.post(action).status_code, 400)
        self.assertEqual(self.post(processId="not-a-process").status_code, 400)
        self.assertEqual(self.post("review", reviewRole=[]).status_code, 400)
