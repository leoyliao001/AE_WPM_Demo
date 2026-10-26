from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from api.models import (
	MigrationIntakeSubmission,
	ProjectAttributesAccess,
	ScopeStatement,
	ScopeStatementLine,
)


class ScopeStatementAccessTests(TestCase):
	def setUp(self):
		self.project = MigrationIntakeSubmission.objects.create(
			migration_request_id="WPM_PRJ_TEST_SCOPE",
			requested_date="26 Oct 2026",
			requestor="requestor@example.com",
			project_name="Scope access test",
			migration_type="Other",
			migration_type_value="other",
			region="APA",
			function_name="Operations",
			proposed_scope="Test scope",
			fte_number="3",
		)
		self.url = f"/api/migration-dashboard/projects/{self.project.id}/scope-statement/"
		self.client = APIClient()

	def test_project_requestor_can_view_and_edit(self):
		response = self.client.get(self.url, HTTP_X_USER_EMAIL="REQUESTOR@example.com")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["canEdit"])

	def test_scope_statement_access_user_can_view_and_edit(self):
		ProjectAttributesAccess.objects.create(
			email="admin@example.com",
			scope_statement=True,
		)

		response = self.client.get(self.url, HTTP_X_USER_EMAIL="admin@example.com")
		save_response = self.client.post(
			f"/api/migration-dashboard/projects/{self.project.id}/scope-statement/save/",
			{"action": "save"},
			format="json",
			HTTP_X_USER_EMAIL="admin@example.com",
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["canEdit"])
		self.assertEqual(save_response.status_code, 200)

	def test_user_without_access_is_denied(self):
		response = self.client.get(self.url, HTTP_X_USER_EMAIL="other@example.com")

		self.assertEqual(response.status_code, 403)

	def test_localhost_development_user_can_view_and_edit(self):
		response = self.client.get(self.url, HTTP_X_USER_EMAIL="local.dev@localhost")

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["canEdit"])

	def test_scope_statement_access_user_can_list_saved_statements(self):
		ProjectAttributesAccess.objects.create(
			email="admin@example.com",
			scope_statement=True,
		)
		statement = ScopeStatement.objects.create(
			project=self.project,
			scope_text="Transfer support operations",
			ambition_fte="3",
		)
		ScopeStatementLine.objects.create(
			statement=statement,
			job_level="JL2",
			agreed_fte="2.5",
		)

		response = self.client.get(
			"/api/migration-dashboard/scope-statements/",
			HTTP_X_USER_EMAIL="admin@example.com",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["count"], 1)
		self.assertEqual(response.data["rows"][0]["project_name"], "Scope access test")
		self.assertEqual(response.data["rows"][0]["scope_text"], "Transfer support operations")
		self.assertEqual(response.data["rows"][0]["jl2_agreed_fte"], "2.5000")

	def test_scope_statement_database_requires_scope_statement_access(self):
		response = self.client.get(
			"/api/migration-dashboard/scope-statements/",
			HTTP_X_USER_EMAIL="other@example.com",
		)

		self.assertEqual(response.status_code, 403)

	def test_access_control_permission_does_not_grant_scope_statement_access(self):
		ProjectAttributesAccess.objects.create(
			email="admin@example.com",
			access_control=True,
			scope_statement=False,
		)

		response = self.client.get(self.url, HTTP_X_USER_EMAIL="admin@example.com")
		admin_list_response = self.client.get(
			"/api/migration-dashboard/scope-statements/",
			HTTP_X_USER_EMAIL="admin@example.com",
		)

		self.assertEqual(response.status_code, 403)
		self.assertEqual(admin_list_response.status_code, 403)

	def test_access_control_user_can_create_update_and_delete_statement(self):
		ProjectAttributesAccess.objects.create(
			email="admin@example.com",
			scope_statement=True,
		)
		url = "/api/migration-dashboard/scope-statements/data/"
		payload = {
			"uniqueData": [{
				"migration_request_id": self.project.migration_request_id,
				"scope_text": "Initial scope",
				"jl2_agreed_fte": "2.5",
				"jl2_not_agreed_fte": "0.5",
				"jl2_final_fte": "2",
			}],
		}

		create_response = self.client.post(
			url,
			payload,
			format="json",
			HTTP_X_USER_EMAIL="admin@example.com",
		)
		self.assertEqual(create_response.status_code, 200)
		self.assertEqual(create_response.data["created_count"], 1)

		statement = ScopeStatement.objects.get(project=self.project)
		payload["uniqueData"][0].update({
			"statement_id": statement.id,
			"scope_text": "Updated scope",
			"jl2_agreed_fte": "2.75",
		})
		update_response = self.client.post(
			url,
			payload,
			format="json",
			HTTP_X_USER_EMAIL="admin@example.com",
		)
		statement.refresh_from_db()
		self.assertEqual(update_response.data["updated_count"], 1)
		self.assertEqual(statement.scope_text, "Updated scope")
		self.assertEqual(statement.lines.get(job_level="JL2").agreed_fte, 2.75)

		delete_response = self.client.delete(
			"/api/migration-dashboard/scope-statements/data/delete/",
			{"removedIds": [statement.id]},
			format="json",
			HTTP_X_USER_EMAIL="admin@example.com",
		)
		self.assertEqual(delete_response.status_code, 200)
		self.assertFalse(ScopeStatement.objects.filter(pk=statement.id).exists())

	def test_admin_cannot_edit_locked_job_level(self):
		ProjectAttributesAccess.objects.create(
			email="admin@example.com",
			scope_statement=True,
		)
		statement = ScopeStatement.objects.create(project=self.project)
		line = ScopeStatementLine.objects.create(
			statement=statement,
			job_level="JL2",
			agreed_fte="2",
			locked_at=timezone.now(),
		)
		response = self.client.post(
			"/api/migration-dashboard/scope-statements/data/",
			{"uniqueData": [{
				"statement_id": statement.id,
				"jl2_agreed_fte": "1",
			}]},
			format="json",
			HTTP_X_USER_EMAIL="admin@example.com",
		)

		line.refresh_from_db()
		self.assertEqual(response.data["error_count"], 1)
		self.assertEqual(line.agreed_fte, 2)


class ScopeStatementAccessControlTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.admin = ProjectAttributesAccess.objects.create(
			email="acl-admin@example.com",
			access_control=True,
			scope_statement=False,
		)
		self.target = ProjectAttributesAccess.objects.create(
			email="scope-user@example.com",
			access_control=True,
		)

	def test_new_access_control_rows_default_scope_statement_to_n(self):
		response = self.client.get(
			"/api/project-attributes-access/",
			HTTP_X_USER_EMAIL=self.admin.email,
		)
		row = next(item for item in response.data["rows"] if item["email"] == self.target.email)

		self.assertEqual(response.status_code, 200)
		self.assertIn(
			{"key": "scope_statement", "label": "Scope Statement (Y/N)"},
			response.data["columns"],
		)
		self.assertEqual(row["scope_statement"], "N")

	def test_existing_scope_statement_values_are_preserved(self):
		previously_allowed = ProjectAttributesAccess.objects.create(
			email="existing-y@example.com",
			access_control=True,
			scope_statement=True,
		)
		response = self.client.get(
			"/api/project-attributes-access/",
			HTTP_X_USER_EMAIL=self.admin.email,
		)
		rows = {item["email"]: item for item in response.data["rows"]}

		self.assertEqual(rows[self.target.email]["scope_statement"], "N")
		self.assertEqual(rows[previously_allowed.email]["scope_statement"], "Y")

	def test_access_control_grid_can_disable_scope_statement_independently(self):
		self.target.scope_statement = True
		self.target.save(update_fields=["scope_statement"])
		response = self.client.get(
			"/api/project-attributes-access/",
			HTTP_X_USER_EMAIL=self.admin.email,
		)
		row = next(item for item in response.data["rows"] if item["email"] == self.target.email)
		row["scope_statement"] = "N"
		row["access_control"] = "Y"

		save_response = self.client.post(
			"/api/project-attributes-access/data/",
			{"uniqueData": [row]},
			format="json",
			HTTP_X_USER_EMAIL=self.admin.email,
		)
		self.target.refresh_from_db()

		self.assertEqual(save_response.status_code, 200)
		self.assertFalse(self.target.scope_statement)
		self.assertTrue(self.target.access_control)

# Create your tests here.
