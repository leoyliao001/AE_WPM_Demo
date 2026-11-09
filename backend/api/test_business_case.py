from copy import deepcopy
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from api.models import (
    ApprovalInput, ApprovalWorkflow, BusinessCase, BusinessCaseCostRate,
    MigrationIntakeSubmission, ProjectAttributesAccess, ScopeStatement, ScopeStatementLine,
)


class OnlineBusinessCaseTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="BC-ONLINE-TEST", requested_date="27 Oct 2026",
            requestor="owner@example.com", project_name="Online BC",
            migration_type="1:1 migration", migration_type_value="one_to_one",
            region="EUR", function_name="Ocean", products=["Documentation"],
            proposed_scope="Transfer documentation", fte_number="98",
            countries=["Denmark"], default_location_strategies=["GSC Mumbai"],
            business_owner="Business Owner", target_start_date="2027-02-01", target_end_date="2027-06-30",
        )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.url = f"/api/migration-dashboard/projects/{self.project.pk}/business-case/"
        self.scope = ScopeStatement.objects.create(project=self.project, scope_text="Locked scope",
                                                   status="submitted", final_project_fte=98)
        for level, count in (("JL2", 58), ("JL3", 30), ("JL4", 10)):
            ScopeStatementLine.objects.create(statement=self.scope, job_level=level, final_fte=count, locked_at=timezone.now())

    def rates(self):
        for level in ("JL2", "JL3", "JL4"):
            for location, annual in (("Denmark", "100000"), ("GSC Mumbai", "25000")):
                BusinessCaseCostRate.objects.create(
                    location=location, job_level=level, annual_cost=annual,
                    currency="USD", usd_rate=1, year=2027, version="FY2027 v1",
                )

    def save(self, **overrides):
        self.project.refresh_from_db()
        record = BusinessCase.objects.filter(project=self.project).first()
        data = {
            "revision": record.revision if record else 0,
            "intakeVersion": self.project.updated_at.isoformat(),
            "sourceVersion": self.client.get(self.url).data.get("sourceVersion"),
            "details": {"rationale": "Consolidate operations", "expectedBenefits": "Standardization",
                        "risks": "KT capacity", "dependencies": "System access", "recommendation": "Proceed"},
            "financialInputs": {"oneTimeCost": "1850000", "adjustment": "150000", "adjustmentReason": "Extra KT travel"},
        }
        data.update(overrides)
        return self.client.post(self.url + "save/", data, format="json")

    def test_get_is_read_only_and_missing_rates_are_not_sample_values(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["saved"])
        self.assertFalse(response.data["financials"]["ready"])
        self.assertIsNone(response.data["financials"]["metrics"]["currentAnnualCost"])
        self.assertFalse(BusinessCase.objects.exists())
        self.assertEqual(response.data["savedSnapshot"], {})

    def test_manual_migratable_fte_flows_to_snapshot_without_changing_cost_basis(self):
        self.rates()
        baseline_response = self.save()
        self.assertEqual(baseline_response.status_code, 200, baseline_response.data)
        baseline = baseline_response.data
        self.scope.migratable_fte = "123.5"
        self.scope.migratable_fte_confirmed = True
        self.scope.save()
        response = self.save(action="submit")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["scope"]["migratableFte"], "123.5000")
        self.assertTrue(response.data["scope"]["migratableFteConfirmed"])
        self.assertEqual(response.data["scope"]["finalProjectFte"], 98)
        self.assertEqual(response.data["financials"]["metrics"], baseline["financials"]["metrics"])
        snapshot = deepcopy(response.data["savedSnapshot"])
        self.assertEqual(snapshot["scope"]["migratableFte"], "123.5000")
        self.scope.migratable_fte = "124"
        self.scope.save()
        record = BusinessCase.objects.get()
        self.assertTrue(record.review_required)
        self.assertEqual(record.saved_snapshot, snapshot)
        current = self.client.get(self.url).data
        self.assertEqual(current["scope"]["migratableFte"], "124.0000")
        self.assertEqual(current["status"], "needs_review")

    def test_complete_snapshot_is_persisted_and_sources_do_not_overwrite_it(self):
        response = self.save()
        self.assertEqual(response.status_code, 200, response.data)
        snapshot = deepcopy(response.data["savedSnapshot"])
        self.assertEqual(snapshot["revision"], 1)
        for field in ("intake", "scope", "details", "financialInputs", "financials", "approval"):
            self.assertEqual(snapshot[field], response.data[field])
        self.assertFalse(snapshot["financials"]["ready"])
        self.assertEqual(snapshot["savedBy"], "owner@example.com")
        record = BusinessCase.objects.get()
        self.assertEqual(record.saved_snapshot, snapshot)
        self.assertEqual(record.financial_history[-1]["pageSnapshot"], snapshot)
        self.project.project_name = "Upstream changed"
        self.project.save()
        self.scope.scope_text = "Changed scope"
        self.scope.save()
        current = self.client.get(self.url).data
        self.assertEqual(current["projectName"], "Upstream changed")
        self.assertEqual(current["savedSnapshot"], snapshot)
        response = self.save(action="refresh", details={"rationale": "New rationale"})
        self.assertEqual(response.status_code, 200, response.data)
        record.refresh_from_db()
        self.assertEqual(record.financial_history[0]["pageSnapshot"], snapshot)
        self.assertEqual(record.saved_snapshot["projectName"], "Upstream changed")
        self.assertEqual(record.saved_snapshot["details"]["rationale"], "New rationale")
        self.assertEqual(record.saved_snapshot["scope"]["scopeText"], "Changed scope")
        self.assertEqual(record.saved_snapshot["revision"], 2)

    def test_failed_or_conflicting_save_does_not_replace_snapshot(self):
        self.save()
        record = BusinessCase.objects.get()
        snapshot = deepcopy(record.saved_snapshot)
        self.assertEqual(self.save(revision=0).status_code, 409)
        self.assertEqual(self.save(action="submit").status_code, 400)
        record.refresh_from_db()
        self.assertEqual(record.saved_snapshot, snapshot)
        self.assertEqual(len(record.financial_history), 1)

    def test_legacy_record_does_not_invent_complete_snapshots(self):
        BusinessCase.objects.create(project=self.project, revision=1)
        self.assertEqual(self.client.get(self.url).data["savedSnapshot"], {})
        self.assertEqual(self.save().status_code, 200)
        self.assertEqual(BusinessCase.objects.get().saved_snapshot["revision"], 2)

    def test_exact_financial_formula_and_adjustment_audit(self):
        self.rates()
        response = self.save()
        self.assertEqual(response.status_code, 200, response.data)
        metrics = response.data["financials"]["metrics"]
        self.assertEqual(metrics, {
            "currentAnnualCost": "9800000.00", "futureAnnualCost": "2450000.00",
            "annualGrossBenefit": "7350000.00", "benefitPercent": "75.00",
            "netFirstYearBenefit": "5350000.00", "recurringAnnualBenefit": "7350000.00",
            "paybackMonths": "3.27", "adjustedOneTimeCost": "2000000.00",
        })
        record = BusinessCase.objects.get()
        self.assertEqual(record.financial_history[0]["inputs"]["adjustmentReason"], "Extra KT travel")
        self.assertEqual(self.client.get(self.url).data["details"]["risks"], "KT capacity")

    def test_currency_conversion_and_zero_fte_levels(self):
        self.rates()
        BusinessCaseCostRate.objects.filter(location="Denmark").update(currency="EUR", usd_rate="1.08")
        response = self.save()
        self.assertEqual(response.data["financials"]["metrics"]["currentAnnualCost"], "10584000.00")
        self.assertEqual(response.data["financials"]["metrics"]["futureAnnualCost"], "2450000.00")

    def test_source_data_is_not_duplicated_or_overwritten(self):
        self.rates()
        response = self.save(scope={"finalProjectFte": 1})
        self.assertEqual(response.status_code, 200)
        self.scope.refresh_from_db()
        self.assertEqual(self.scope.final_project_fte, 98)
        record = BusinessCase.objects.get()
        self.assertNotIn("scope", record.details)

    def test_intake_edit_writes_same_record_and_audits_changes(self):
        response = self.save(intake={"project_name": "Updated original", "initial_rationale": "Rationale"})
        self.assertEqual(response.status_code, 200, response.data)
        self.project.refresh_from_db()
        self.assertEqual(self.project.project_name, "Updated original")
        self.assertEqual(MigrationIntakeSubmission.objects.count(), 1)
        self.assertEqual(self.project.intake_audit_log[-1]["changes"]["project_name"]["old"], "Online BC")

    def test_invalid_submit_rolls_back_intake_and_record(self):
        response = self.save(action="submit", intake={"project_name": "Must rollback"})
        self.assertEqual(response.status_code, 400)
        self.project.refresh_from_db()
        self.assertEqual(self.project.project_name, "Online BC")
        self.assertFalse(BusinessCase.objects.exists())
        self.assertIsNone(self.project.business_case_submission_date)

    def test_controlled_intake_choices_and_derived_values(self):
        response = self.save(intake={
            "migration_type": "Co-Location", "region": "EUR", "areas": ["NDC"],
            "countries": ["Denmark"], "default_location_strategies": ["Chennai"],
            "function_name": "Customer Experience", "products": ["General Ocean"],
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.project.refresh_from_db()
        self.assertEqual(self.project.migration_type_value, "co-location")
        self.assertEqual(self.project.area_country_pairs, [{"area": "NDC", "country": "Denmark"}])

    def test_invalid_intake_selections_roll_back(self):
        for intake in (
            {"migration_type": "Made up"},
            {"region": "Unknown"},
            {"areas": ["NDC"], "countries": ["India"]},
            {"function_name": "Customer Experience", "products": ["Made up"]},
            {"areas": ["NDC"], "default_location_strategies": ["Mumbai"]},
            {"location_strategy_custom": True, "custom_location_strategies": ["Pune"]},
            {"target_start_date": "2027-07-01", "target_end_date": "2027-06-01"},
        ):
            with self.subTest(intake=intake):
                response = self.save(intake=intake)
                self.assertEqual(response.status_code, 400, response.data)
                self.assertFalse(BusinessCase.objects.exists())
        self.project.refresh_from_db()
        self.assertEqual(self.project.areas, [])

    def test_parent_change_requires_review_of_legacy_child_values(self):
        response = self.save(intake={"region": "APA", "areas": ["NDC"]})
        self.assertEqual(response.status_code, 400, response.data)
        response = self.save(intake={"business_owner": "Updated Owner"})
        self.assertEqual(response.status_code, 200, response.data)

    def test_multiple_valid_choices_remain_supported_for_drafts(self):
        response = self.save(intake={
            "areas": ["NDC"], "countries": ["Denmark", "Sweden"],
            "default_location_strategies": ["Chennai", "Poland"],
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data["financials"]["ready"])

    def test_invalid_numbers_and_request_shapes_are_rejected(self):
        for value in ("NaN", "Infinity", True, "-1", "100000000000000"):
            with self.subTest(value=value):
                self.assertEqual(self.save(financialInputs={"oneTimeCost": value}).status_code, 400)
        for payload in ([], "bad"):
            self.assertEqual(self.client.post(self.url + "save/", payload, format="json").status_code, 400)
        self.assertEqual(self.save(action=[]).status_code, 400)
        self.assertFalse(BusinessCase.objects.exists())

    def test_adjustment_requires_reason_and_nonnegative_adjusted_value(self):
        self.assertEqual(self.save(financialInputs={"oneTimeCost": "10", "adjustment": "2"}).status_code, 400)
        self.assertEqual(self.save(financialInputs={"oneTimeCost": "10", "adjustment": "-11", "adjustmentReason": "Invalid"}).status_code, 400)

    def test_revision_and_intake_version_conflicts(self):
        self.save()
        self.assertEqual(self.save(revision=0).status_code, 409)
        self.assertEqual(self.save(revision=True).status_code, 409)
        self.assertEqual(self.save(intakeVersion="old").status_code, 409)
        self.assertEqual(self.save(sourceVersion="old").status_code, 409)

    def test_access_and_admin_permissions(self):
        self.client.credentials()
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.credentials(HTTP_X_USER_EMAIL="stranger@example.com")
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.save().status_code, 403)
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        self.assertEqual(self.client.get("/api/migration-dashboard/business-cases/").status_code, 403)
        ProjectAttributesAccess.objects.create(email="maintainer@example.com", business_case=True)
        self.client.credentials(HTTP_X_USER_EMAIL="maintainer@example.com")
        self.assertEqual(self.save().status_code, 200)
        self.assertEqual(self.save(action="submit").status_code, 403)
        self.assertEqual(self.client.get("/api/migration-dashboard/business-cases/").status_code, 200)

    @patch("api.views.approval_cycle._notify_next_approvers")
    def test_super_admin_must_revise_submitted_case_and_cannot_submit_for_owner(self, notify):
        self.rates()
        response = self.save(action="submit")
        self.assertEqual(response.status_code, 200, response.data)
        ProjectAttributesAccess.objects.create(email="admin@example.com", is_super_admin=True)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@example.com")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data["canEdit"])
        self.assertEqual(self.save().status_code, 409)
        self.assertEqual(self.save(action="revise", reason="").status_code, 400)
        response = self.save(action="revise", reason="Admin correction")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["canEdit"])
        response = self.save(details={"rationale": "Admin corrected rationale"})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["updatedBy"], "admin@example.com")
        self.assertEqual(response.data["history"][-2]["reason"], "Admin correction")
        self.assertEqual(self.save(action="submit").status_code, 403)

    @patch("api.views.approval_cycle._notify_next_approvers")
    def test_online_submit_starts_existing_workflow_without_file(self, notify):
        self.rates()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.save(action="submit")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "submitted")
        self.assertFalse(response.data["canEdit"])
        self.assertTrue(ApprovalWorkflow.objects.filter(migration_request_id=self.project.migration_request_id).exists())
        self.assertEqual(response.data["savedSnapshot"]["status"], "submitted")
        self.assertEqual(response.data["savedSnapshot"]["approval"], response.data["approval"])
        self.project.refresh_from_db()
        self.assertIsNotNone(self.project.business_case_submission_date)
        self.assertFalse(self.project.business_case_file)
        notify.assert_called_once()
        self.assertEqual(self.save().status_code, 409)
        self.assertEqual(self.client.post(self.url + "submit/", {}, format="json").status_code, 409)

    def test_cost_change_flags_review_and_blocks_approval(self):
        self.rates()
        self.save(action="submit")
        rate = BusinessCaseCostRate.objects.first()
        rate.annual_cost += 100
        rate.save()
        record = BusinessCase.objects.get()
        self.assertTrue(record.review_required)
        self.assertEqual(self.client.get(self.url).data["status"], "needs_review")
        self.assertEqual(record.audit_log[-1]["action"], "source_changed")
        response = self.client.post("/api/approval-cycle/decision/", {
            "migration_request_id": self.project.migration_request_id, "role": "area_head", "action": "approved",
        }, format="json")
        self.assertEqual(response.status_code, 409)

    def test_intake_change_flags_review_preserves_submitted_calculation(self):
        self.rates()
        self.save(action="submit")
        record = BusinessCase.objects.get()
        historical = record.financial_history[-1]["financials"]["metrics"]
        self.project.project_name = "Upstream update"
        self.project.save()
        data = self.client.get(self.url).data
        self.assertTrue(data["reviewRequired"])
        self.assertEqual(data["details"]["rationale"], "Consolidate operations")
        self.assertEqual(data["financialHistory"][-1]["financials"]["metrics"], historical)

    def test_scope_change_requires_reapproval(self):
        self.rates()
        self.save(action="submit")
        line = self.scope.lines.get(job_level="JL2")
        line.final_fte = 59
        line.save()
        self.assertEqual(self.client.get(self.url).data["status"], "needs_review")
        self.assertFalse(self.client.get(self.url).data["financials"]["ready"])

    def test_revise_requires_reason_resets_workflow_and_preserves_history(self):
        self.rates()
        self.save(action="submit")
        workflow = ApprovalWorkflow.objects.get()
        workflow.area_head_status = "approved"
        workflow.save()
        self.assertEqual(self.save(action="revise").status_code, 400)
        response = self.save(action="revise", reason="Update costs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "returned")
        workflow.refresh_from_db()
        self.assertEqual(workflow.area_head_status, "")
        self.assertIsNone(workflow.business_case_submitted_date)
        record = BusinessCase.objects.get()
        self.assertEqual(record.audit_log[-1]["old"]["approval"]["area_head_status"], "approved")

    def test_negative_benefit_has_no_fake_payback(self):
        self.rates()
        BusinessCaseCostRate.objects.filter(location="GSC Mumbai").update(annual_cost="200000")
        response = self.save()
        self.assertIsNone(response.data["financials"]["metrics"]["paybackMonths"])
        self.assertEqual(response.data["financials"]["metrics"]["annualGrossBenefit"], "-9800000.00")

    def test_zero_denominators_are_explicit_and_never_divide_by_zero(self):
        self.rates()
        BusinessCaseCostRate.objects.all().update(annual_cost=0)
        response = self.save()
        self.assertTrue(response.data["financials"]["ready"])
        self.assertIsNone(response.data["financials"]["metrics"]["benefitPercent"])
        self.assertIsNone(response.data["financials"]["metrics"]["paybackMonths"])
        self.assertEqual(response.data["financials"]["metrics"]["annualGrossBenefit"], "0.00")
        self.assertGreaterEqual(len(response.data["financials"]["warnings"]), 2)

    def test_multiple_locations_are_blocked_without_allocation(self):
        self.project.countries = ["Denmark", "Sweden"]
        self.project.save()
        response = self.save()
        self.assertFalse(response.data["financials"]["ready"])
        self.assertIn("Multi-location", " ".join(response.data["financials"]["errors"]))
        self.assertEqual(self.save(action="submit").status_code, 400)

    def test_admin_delete_keeps_sources_and_rejects_stale_revision(self):
        self.save()
        self.client.credentials(HTTP_X_USER_EMAIL="admin@localhost")
        self.assertEqual(self.client.post(self.url + "delete/", {"revision": 0}, format="json").status_code, 409)
        self.assertEqual(self.client.post(self.url + "delete/", {"revision": 1}, format="json").status_code, 200)
        self.assertTrue(ScopeStatement.objects.filter(pk=self.scope.pk).exists())
        self.assertTrue(MigrationIntakeSubmission.objects.filter(pk=self.project.pk).exists())

    def test_cost_rate_crud_validation_and_stale_write_protection(self):
        url = "/api/migration-dashboard/cost-rates/"
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.credentials(HTTP_X_USER_EMAIL="admin@localhost")
        payload = {"location": "Denmark", "jobLevel": "JL2", "year": 2027, "annualCost": "100000", "currency": "USD", "usdRate": "1", "version": "FY2027"}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        item = response.data
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 400)
        payload.update(id=item["id"], updatedAt="old")
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 409)
        payload["updatedAt"] = item["updatedAt"]
        payload["annualCost"] = "120000"
        updated = self.client.post(url, payload, format="json")
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(self.client.delete(url + str(item["id"]) + "/", {"updatedAt": item["updatedAt"]}, format="json").status_code, 409)
        self.assertEqual(self.client.delete(url + str(item["id"]) + "/", {"updatedAt": updated.data["updatedAt"]}, format="json").status_code, 200)

    @patch("api.views.approval_cycle._notify_next_approvers")
    def test_existing_role_chain_approves_the_online_record_and_charter(self, notify):
        self.rates()
        self.save(action="submit")
        ApprovalInput.objects.create(
            activity_function="Ocean", product="Documentation", area_head="approver@example.com",
            pmo="approver@example.com", bpm="approver@example.com", wpm="approver@example.com",
            elt="approver@example.com", gsc_head="approver@example.com",
        )
        self.client.credentials(HTTP_X_USER_EMAIL="approver@example.com")
        for role in ("area_head", "pmo", "bpm", "wpm", "elt", "gsc_head"):
            with self.subTest(role=role):
                response = self.client.post("/api/approval-cycle/decision/", {
                    "migration_request_id": self.project.migration_request_id, "role": role,
                    "action": "approved", "budget_status": "within",
                }, format="json")
                self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.client.get(self.url).data["status"], "approved")
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        charter = self.client.get(f"/api/migration-dashboard/projects/{self.project.pk}/project-charter/").data
        self.assertTrue(charter["sources"]["completeness"][1]["complete"])
        self.assertEqual(charter["sources"]["risks"], "KT capacity")
        rate = BusinessCaseCostRate.objects.first()
        rate.delete()
        charter = self.client.get(f"/api/migration-dashboard/projects/{self.project.pk}/project-charter/").data
        self.assertFalse(charter["sources"]["completeness"][1]["complete"])
        self.assertEqual(self.client.get(self.url).data["status"], "needs_review")

    def test_scope_extensions_persist_only_in_scope_and_reopening_flags_review(self):
        self.rates()
        self.save(action="submit")
        scope_url = f"/api/migration-dashboard/projects/{self.project.pk}/scope-statement/"
        self.assertEqual(self.client.post(scope_url + "save/", {"action": "submit", "scopeText": "Forged"}, format="json").status_code, 409)
        response = self.client.post(scope_url + "save/", {"action": "revise", "reason": "Add wave detail"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.client.get(self.url).data["status"], "needs_review")
        response = self.client.post(scope_url + "save/", {"action": "unlock"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        response = self.client.post(scope_url + "save/", {
            "outOfScope": "Customer escalations", "assumptions": "English only",
            "waves": [{"name": "Wave 1", "date": "2027-02-01", "fte": 98}],
        }, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.client.get(self.url).data["scope"]["outOfScope"], "Customer escalations")
        self.assertEqual(self.client.get(self.url).data["scope"]["waves"][0]["fte"], 98)
        for waves in ([{"name": "Invalid", "date": "bad", "fte": 1}], [{"name": "", "date": "2027-02-01", "fte": -1}]):
            self.assertEqual(self.client.post(scope_url + "save/", {"waves": waves}, format="json").status_code, 400)

    def test_scope_input_edits_flag_submitted_scope_for_review(self):
        response = self.save(intake={"target_start_date": "2027-03-01"})
        self.assertEqual(response.status_code, 200, response.data)
        self.scope.refresh_from_db()
        self.assertTrue(self.scope.review_required)
        self.assertTrue(response.data["scope"]["reviewRequired"])
        self.assertFalse(response.data["financials"]["ready"])
        self.assertEqual(self.scope.audit_log[-1]["action"], "intake_changed")

    def test_stale_scope_or_rate_snapshot_cannot_be_submitted(self):
        self.rates()
        source_version = self.client.get(self.url).data["sourceVersion"]
        rate = BusinessCaseCostRate.objects.first()
        rate.annual_cost += 1
        rate.save()
        response = self.save(action="submit", sourceVersion=source_version)
        self.assertEqual(response.status_code, 409)
        self.assertFalse(BusinessCase.objects.exists())

    def test_queue_disables_approval_for_changed_sources(self):
        self.rates()
        self.save(action="submit")
        self.project.project_name = "Review-required project"
        self.project.save()
        ApprovalInput.objects.create(activity_function="Ocean", product="Documentation", area_head="approver@example.com")
        self.client.credentials(HTTP_X_USER_EMAIL="approver@example.com")
        response = self.client.get("/api/approval-cycle/queue/")
        self.assertEqual(response.status_code, 200)
        row = next(item for item in response.data["rows"] if item["migration_request_id"] == self.project.migration_request_id)
        self.assertEqual(row["businessCaseStatus"], "needs_review")
        self.assertTrue(row["businessCaseBlocked"])
        self.assertFalse(row["completed"])
        self.assertFalse(row["actionable"])
