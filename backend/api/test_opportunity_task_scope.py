from django.test import TestCase
from rest_framework.test import APIClient

from api.models import MigrationIntakeSubmission, OpportunityAssessment, OpportunityAssessmentScope
from api.views.opportunity_task_scope import _catalogue


class OpportunityTaskScopeTests(TestCase):
    def setUp(self):
        self.project = MigrationIntakeSubmission.objects.create(
            migration_request_id="OA-SCOPE-TEST", requested_date="2026-11-02", requestor="owner@example.com",
            project_name="Scope test", migration_type="1:1 Transfer", migration_type_value="1:1-transfer",
            region="APA", areas=["SEA"], countries=["Singapore", "Malaysia"],
            function_name="CX", products=["LCL"], proposed_scope="Test", fte_number="1",
        )
        self.client = APIClient()
        self.client.credentials(HTTP_X_USER_EMAIL=self.project.requestor)
        self.url = f"/api/migration-dashboard/projects/{self.project.pk}/opportunity-assessment/task-scope/"

    def row(self, ref=0, row_id="t1"):
        item = _catalogue()[ref]
        return {"id": row_id, "ref": ref, "ctry": "Singapore; Malaysia", "loc": "Manila",
                "p": item[0], "l1": item[1], "l2": item[2], "l3": item[3], "l4": item[4],
                "task": "Task", "desc": "Details", "cx": "High", "sop": "Y", "freq": "Daily",
                "uom": "Cases", "vol": "400", "tpu": "2", "mgsc": "Yes", "exc": "Language Barrier"}

    def save(self, state, revision=0, **extra):
        return self.client.post(self.url, {"migration_request_id": self.project.migration_request_id,
                                         "state": state, "revision": revision, **extra}, format="json")

    def test_round_trip_both_modes_and_sync_active_rows(self):
        state = {"cat": [self.row(0, "c0")], "task": [self.row(1)], "seq": 2, "mode": "task"}
        response = self.save(state)
        self.assertEqual(response.status_code, 200, response.data)
        row = OpportunityAssessment.objects.get()
        self.assertEqual(row.fte_calculation, "2.0000")
        self.assertEqual(row.scope_details["exc"], "Language Barrier")
        self.assertEqual(row.scope_details["ctry"], "Singapore; Malaysia")
        loaded = self.client.get(self.url).data
        self.assertEqual(loaded["state"]["task"][0]["desc"], "Details")
        self.assertEqual(len(loaded["state"]["cat"]), 1)
        loaded["state"]["mode"] = "cat"
        response = self.save(loaded["state"], revision=1)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(OpportunityAssessment.objects.count(), 1)
        self.assertEqual(OpportunityAssessment.objects.get().scope_details["method"], "cat")
        self.assertEqual(len(response.data["state"]["task"]), 1)

    def test_invalid_upload_is_atomic_and_wrong_project_is_rejected(self):
        state = {"cat": None, "task": [self.row()], "seq": 2, "mode": "task"}
        response = self.save(state, migration_request_id="ANOTHER-PROJECT")
        self.assertEqual(response.status_code, 400)
        state["task"][0]["vol"] = "NaN"
        self.assertEqual(self.save(state).status_code, 400)
        self.assertFalse(OpportunityAssessmentScope.objects.exists())
        self.assertFalse(OpportunityAssessment.objects.exists())

    def test_complete_catalogue_can_be_saved_without_truncation(self):
        rows = [self.row(index, f"c{index}") for index in range(len(_catalogue()))]
        state = {"cat": rows, "task": [], "seq": 1, "mode": "cat"}
        response = self.save(state)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(OpportunityAssessment.objects.count(), len(_catalogue()))
        self.assertEqual(self.save(response.data["state"], revision=1).status_code, 200)
        self.assertEqual(OpportunityAssessment.objects.count(), len(_catalogue()))

    def test_intake_product_alias_preserves_display_name(self):
        self.project.products = ["General LCL"]
        self.project.save()
        intake = self.client.get(self.url).data["intake"]
        self.assertEqual(intake["product"], "General LCL")
        self.assertEqual(intake["catalogue_products"], ["LCL"])

    def test_country_and_duplicate_validation(self):
        state = {"cat": None, "task": [self.row()], "seq": 2, "mode": "task"}
        state["task"][0]["ctry"] = "Denmark"
        self.assertEqual(self.save(state).status_code, 400)
        state["task"] = [self.row(), self.row()]
        self.assertEqual(self.save(state).status_code, 400)

    def test_stale_save_cannot_overwrite_and_delete_is_persisted(self):
        state = {"cat": None, "task": [self.row()], "seq": 2, "mode": "task"}
        self.assertEqual(self.save(state).status_code, 200)
        state["task"] = []
        self.assertEqual(self.save(state).status_code, 409)
        self.assertEqual(OpportunityAssessment.objects.count(), 1)
        self.assertEqual(self.save(state, revision=1).status_code, 200)
        self.assertEqual(OpportunityAssessment.objects.count(), 0)
        self.assertEqual(self.client.get(self.url).data["state"]["task"], [])

    def test_legacy_rows_are_preserved_on_first_load(self):
        OpportunityAssessment.objects.create(migration_request_id=self.project.migration_request_id,
                                             product="Legacy", task_name="Existing task", l3="Legacy L3", upstream="Original upstream", sop_iop_exists="Yes")
        response = self.client.get(self.url)
        self.assertEqual(response.data["state"]["mode"], "task")
        self.assertEqual(response.data["state"]["task"][0]["sop"], "Y")
        state = response.data["state"]
        state["task"][0]["exc"] = "Legal Issues"
        self.assertEqual(self.save(state).status_code, 200)
        self.assertEqual(OpportunityAssessment.objects.get().task_name, "Existing task")
        state["cat"] = [self.row(0, "c0")]
        state["mode"] = "cat"
        self.assertEqual(self.save(state, revision=1).status_code, 200)
        state["mode"] = "task"
        self.assertEqual(self.save(state, revision=2).status_code, 200)
        self.assertEqual(OpportunityAssessment.objects.get().upstream, "Original upstream")

    def test_access_control_and_project_isolation(self):
        self.client.credentials(HTTP_X_USER_EMAIL="other@example.com")
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.save({}).status_code, 403)
        self.client.credentials()
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.credentials(HTTP_X_USER_EMAIL=self.project.requestor)
        OpportunityAssessment.objects.create(migration_request_id="OTHER", task_name="Other task")
        self.assertEqual(self.client.get(self.url).data["state"]["task"], [])