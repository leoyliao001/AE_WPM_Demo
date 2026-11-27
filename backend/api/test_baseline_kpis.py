from django.test import TestCase
from rest_framework.test import APIClient

from api.models import (
    BaselineKpiRecord,
    MigrationIntakeSubmission,
    MigrationTeam,
    OpportunityAssessment,
    OpportunityAssessmentScope,
    ProjectResources,
    StakeholderRegistration,
)


class BaselineKpiTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="KPI-TEST",
            requested_date="2026-01-01",
            requestor="owner@example.com",
            project_name="KPI test project",
            migration_type="Full",
            migration_type_value="Full migration",
            region="EUR",
            areas=["CSE"],
            countries=["Croatia"],
            target_start_date="2026-02-01",
            function_name="Finance",
            proposed_scope="Project scope",
            fte_number="2",
        )
        self.manager = MigrationTeam.objects.create(role="Manager", email="manager@example.com")
        StakeholderRegistration.objects.create(
            project=self.project,
            team_members=[
                {"id": "area-poc", "email": "area-poc@example.com", "fullName": "Area POC"},
                {"id": "area-sme", "email": "area-sme@example.com", "fullName": "Area SME"},
                {"id": "gsc-sme", "email": "gsc-sme@example.com", "fullName": "GSC SME"},
                {"id": "gsc-leader", "email": "gsc-leader@example.com", "fullName": "GSC Leader"},
            ],
            assignments={
                "area_poc": {"personIds": ["area-poc"], "lockedAt": "2026-01-01"},
                "area_sme": {"personIds": ["area-sme"], "lockedAt": "2026-01-01"},
                "gsc_sme": {"personIds": ["gsc-sme"], "lockedAt": "2026-01-01"},
                "gsc_leaders": {"personIds": ["gsc-leader"], "lockedAt": "2026-01-01"},
                "migration_manager": {
                    "personIds": [f"migration-team-{self.manager.pk}"],
                    "lockedAt": "2026-01-01",
                },
            },
        )
        ProjectResources.objects.create(
            project=self.project,
            rows=[
                {"id": "r1", "cohort": "Cohort A"},
                {"id": "r2", "cohort": "Cohort A"},
                {"id": "r3", "cohort": "Cohort B"},
                {"id": "r4", "cohort": ""},
            ],
        )
        OpportunityAssessmentScope.objects.create(
            project=self.project,
            state={
                "mode": "cat",
                "catGroups": [
                    {
                        "id": "group-1",
                        "rows": [
                            {"id": "oa-1", "l2": "Order Management", "l3": "Create Order", "l4": "Create Sales Order"},
                            {"id": "oa-2", "l2": "Billing & Invoicing", "l3": "Invoice Check", "l4": "Validate Invoice"},
                        ],
                    },
                ],
            },
        )
        self.client = APIClient()
        self.url = f"/api/migration-dashboard/projects/{self.project.pk}/baseline-kpis/"

    def kpi(self, **overrides):
        return {
            "id": "kpi-1",
            "process": ["Create Order"],
            "dimension": "Service",
            "kpi": "Invoice processing SLA",
            "definition": "Invoices processed within target time",
            "frequency": "Weekly",
            "globalTarget": "97",
            "areaBaseline": "95",
            "measure": ">=",
            "targetBaseline": "Area",
            "weeklyValues": [None, None, None, None],
            **overrides,
        }

    def save_setup(self, cohort_name="Cohort A", countries=None, **kpi_overrides):
        self.client.credentials(HTTP_X_USER_EMAIL="area-poc@example.com")
        response = self.client.put(
            self.url,
            {
                "action": "setup",
                "revision": 0,
                "cohort": {
                    "name": cohort_name,
                    "countries": countries or ["Croatia"],
                    "startDate": "2026-02-01",
                    "kpis": [self.kpi(**kpi_overrides)],
                },
            },
            format="json",
        )
        return response

    def test_get_uses_resource_cohorts_and_intake_region_area_countries(self):
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual([cohort["name"] for cohort in response.data["cohorts"]], ["Cohort A", "Cohort B"])
        self.assertIn("Croatia", response.data["countries"])
        self.assertNotIn("Canada", response.data["countries"])
        self.assertEqual(response.data["processOptions"], ["Create Order", "Invoice Check"])
        self.assertEqual(response.data["permissions"]["people"]["areaPoc"], ["Area POC"])

    def test_process_options_follow_l3_values_from_the_active_task_method(self):
        scope = OpportunityAssessmentScope.objects.get(project=self.project)
        scope.state = {
            "mode": "task",
            "task": [
                {"id": "task-1", "l2": "Order Management", "l3": "Amend Order", "l4": "Update Existing Order"},
                {"id": "task-2", "l2": "Billing & Invoicing", "l3": "Invoice Reconciliation", "l4": "Reconcile Invoice"},
            ],
            "catGroups": [
                {"id": "stale", "rows": [{"l2": "Old Process", "l3": "Inactive L3", "l4": "Inactive L4"}]},
            ],
        }
        scope.save(update_fields=["state"])

        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["processOptions"],
            ["Amend Order", "Invoice Reconciliation"],
        )

    def test_process_options_fall_back_to_legacy_assessment_l3_values(self):
        OpportunityAssessmentScope.objects.filter(project=self.project).delete()
        OpportunityAssessment.objects.create(
            migration_request_id=self.project.migration_request_id,
            l2="Order Management",
            l3="Order Release",
            l4="Release Sales Order",
        )
        OpportunityAssessment.objects.create(
            migration_request_id=self.project.migration_request_id,
            l2="Order Management",
            l3="",
            l4="Should Not Be Used",
        )

        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["processOptions"], ["Order Release"])

    def test_setup_rejects_process_not_selected_in_opportunity_assessment(self):
        response = self.save_setup(process=["Order-to-Cash"])
        self.assertEqual(response.status_code, 400)
        self.assertIn("valid Process values", response.data["error"])

    def test_setup_accepts_multiple_selected_l3_processes(self):
        response = self.save_setup(process=["Create Order", "Invoice Check"])

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["cohorts"][0]["kpis"][0]["process"],
            ["Create Order", "Invoice Check"],
        )

    def test_existing_single_process_value_is_returned_as_a_selection_list(self):
        legacy_kpi = self.kpi(process="Order Management")
        BaselineKpiRecord.objects.create(
            project=self.project,
            state={
                "cohorts": {
                    "Cohort A": {
                        "setupSubmitted": True,
                        "kpis": [legacy_kpi],
                    },
                },
            },
        )

        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["cohorts"][0]["kpis"][0]["process"],
            ["Order Management"],
        )

    def test_weekly_results_are_rejected_until_kpi_setup_is_saved(self):
        self.client.credentials(HTTP_X_USER_EMAIL="gsc-sme@example.com")
        response = self.client.put(
            self.url,
            {
                "action": "weekly",
                "revision": 0,
                "cohortName": "Cohort A",
                "kpis": [{"id": "kpi-1", "weeklyValues": [None, None, None, None]}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Save the KPI setup", response.data["error"])

    def test_setup_and_weekly_saves_are_separated_by_assigned_roles(self):
        self.client.credentials(HTTP_X_USER_EMAIL="owner@example.com")
        denied = self.client.put(
            self.url,
            {"action": "setup", "revision": 0, "cohort": {}},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)

        setup = self.save_setup()
        self.assertEqual(setup.status_code, 200, setup.data)
        self.assertTrue(setup.data["cohorts"][0]["setupSubmitted"])
        self.assertTrue(setup.data["cohorts"][0]["setupLocked"])
        self.assertEqual(setup.data["revision"], 1)
        self.assertNotIn("comments", setup.data["cohorts"][0]["kpis"][0])

        record = BaselineKpiRecord.objects.get(project=self.project)
        record.state["cohorts"]["Cohort A"]["kpis"][0]["comments"] = ["legacy"] * 4
        record.save(update_fields=["state"])

        self.client.credentials(HTTP_X_USER_EMAIL="gsc-sme@example.com")
        weekly = self.client.put(
            self.url,
            {
                "action": "weekly",
                "revision": 1,
                "cohortName": "Cohort A",
                "kpis": [{
                    "id": "kpi-1",
                    "weeklyValues": ["90", None, None, None],
                }],
            },
            format="json",
        )
        self.assertEqual(weekly.status_code, 200, weekly.data)
        self.assertEqual(weekly.data["revision"], 2)
        stored_kpi = BaselineKpiRecord.objects.get(project=self.project).state["cohorts"]["Cohort A"]["kpis"][0]
        self.assertEqual(stored_kpi["weeklyValues"][0], "90")
        self.assertNotIn("comments", stored_kpi)

    def test_setup_lock_requires_manager_unlock_reason_and_relocks_on_save(self):
        setup = self.save_setup()
        self.assertEqual(setup.status_code, 200, setup.data)

        self.client.credentials(HTTP_X_USER_EMAIL="area-poc@example.com")
        locked_edit = self.client.put(
            self.url,
            {
                "action": "setup",
                "revision": 1,
                "cohort": {
                    "name": "Cohort A",
                    "countries": ["Croatia"],
                    "startDate": "2026-02-01",
                    "kpis": [self.kpi(kpi="Updated KPI")],
                },
            },
            format="json",
        )
        self.assertEqual(locked_edit.status_code, 400)
        self.assertIn("setup is locked", locked_edit.data["error"])

        denied = self.client.put(
            self.url,
            {
                "action": "unlock",
                "revision": 1,
                "cohortName": "Cohort A",
                "reason": "Approved change.",
            },
            format="json",
        )
        self.assertEqual(denied.status_code, 403)

        self.client.credentials(HTTP_X_USER_EMAIL="manager@example.com")
        missing_reason = self.client.put(
            self.url,
            {"action": "unlock", "revision": 1, "cohortName": "Cohort A", "reason": " "},
            format="json",
        )
        self.assertEqual(missing_reason.status_code, 400)

        unlocked = self.client.put(
            self.url,
            {
                "action": "unlock",
                "revision": 1,
                "cohortName": "Cohort A",
                "reason": "Approved KPI definition change.",
            },
            format="json",
        )
        self.assertEqual(unlocked.status_code, 200, unlocked.data)
        cohort = unlocked.data["cohorts"][0]
        self.assertFalse(cohort["setupLocked"])
        self.assertEqual(cohort["setupUnlockHistory"][-1]["by"], "manager@example.com")
        self.assertEqual(
            cohort["setupUnlockHistory"][-1]["reason"],
            "Approved KPI definition change.",
        )

        relocked = self.client.put(
            self.url,
            {
                "action": "setup",
                "revision": 2,
                "cohort": {
                    "name": "Cohort A",
                    "countries": ["Croatia"],
                    "startDate": "2026-02-01",
                    "kpis": [self.kpi(kpi="Updated KPI")],
                },
            },
            format="json",
        )
        self.assertEqual(relocked.status_code, 200, relocked.data)
        self.assertTrue(relocked.data["cohorts"][0]["setupLocked"])
        stored = BaselineKpiRecord.objects.get(project=self.project).state["cohorts"]["Cohort A"]
        self.assertEqual(stored["setupUnlockHistory"][-1]["reason"], "Approved KPI definition change.")

    def test_additional_comments_are_persisted_and_limited_to_500_characters(self):
        too_long = self.save_setup(additionalComments="x" * 501)
        self.assertEqual(too_long.status_code, 400)
        self.assertIn("at most 500 characters", too_long.data["error"])
        self.assertFalse(BaselineKpiRecord.objects.exists())

        comments = "x" * 500
        setup = self.save_setup(additionalComments=comments)
        self.assertEqual(setup.status_code, 200, setup.data)
        self.assertEqual(setup.data["cohorts"][0]["kpis"][0]["additionalComments"], comments)
        stored_kpi = BaselineKpiRecord.objects.get(project=self.project).state["cohorts"]["Cohort A"]["kpis"][0]
        self.assertEqual(stored_kpi["additionalComments"], comments)

    def test_details_and_comments_can_be_saved_without_unlocking_kpi_definitions(self):
        setup = self.save_setup()
        self.assertEqual(setup.status_code, 200, setup.data)

        details = self.client.put(
            self.url,
            {
                "action": "details",
                "revision": 1,
                "cohort": {
                    "name": "Cohort A",
                    "countries": ["Croatia"],
                    "startDate": "2026-03-01",
                    "kpis": [{
                        "id": "kpi-1",
                        "additionalComments": "Review with the regional team.",
                        "kpi": "Attempt to change a locked definition",
                    }],
                },
            },
            format="json",
        )
        self.assertEqual(details.status_code, 200, details.data)
        cohort = details.data["cohorts"][0]
        self.assertTrue(cohort["setupLocked"])
        self.assertEqual(cohort["startDate"], "2026-03-01")
        self.assertEqual(cohort["kpis"][0]["kpi"], "Invoice processing SLA")
        self.assertEqual(
            cohort["kpis"][0]["additionalComments"],
            "Review with the regional team.",
        )

    def test_country_cannot_be_assigned_to_multiple_cohorts(self):
        first = self.save_setup()
        self.assertEqual(first.status_code, 200, first.data)
        self.client.credentials(HTTP_X_USER_EMAIL="area-poc@example.com")
        duplicate = self.client.put(
            self.url,
            {
                "action": "setup",
                "revision": 1,
                "cohort": {
                    "name": "Cohort B",
                    "countries": ["Croatia"],
                    "startDate": "2026-02-01",
                    "kpis": [self.kpi(id="kpi-2")],
                },
            },
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("only be assigned to one Cohort", duplicate.data["error"])

    def test_setup_rejects_non_integer_baseline_targets(self):
        response = self.save_setup(globalTarget="97.5")
        self.assertEqual(response.status_code, 400)
        self.assertIn("whole number", response.data["error"])
        self.assertFalse(BaselineKpiRecord.objects.exists())

    def test_extension_requires_week_role_reason_and_stays_within_ten_weeks(self):
        setup = self.save_setup()
        self.assertEqual(setup.status_code, 200, setup.data)
        self.client.credentials(HTTP_X_USER_EMAIL="gsc-sme@example.com")
        no_reason = self.client.put(
            self.url,
            {
                "action": "extend",
                "revision": 1,
                "cohortName": "Cohort A",
                "additionalWeeks": 1,
                "reason": " ",
            },
            format="json",
        )
        self.assertEqual(no_reason.status_code, 400)

        extension = self.client.put(
            self.url,
            {
                "action": "extend",
                "revision": 1,
                "cohortName": "Cohort A",
                "additionalWeeks": 6,
                "reason": "Additional transition monitoring required.",
            },
            format="json",
        )
        self.assertEqual(extension.status_code, 200, extension.data)
        self.assertEqual(extension.data["cohorts"][0]["weeks"], 10)

        too_many = self.client.put(
            self.url,
            {
                "action": "extend",
                "revision": 2,
                "cohortName": "Cohort A",
                "additionalWeeks": 1,
                "reason": "One more week.",
            },
            format="json",
        )
        self.assertEqual(too_many.status_code, 400)
        self.assertIn("must not exceed 10", too_many.data["error"])
