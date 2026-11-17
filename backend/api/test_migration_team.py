from django.test import TestCase
from rest_framework.test import APIClient

from api.models import MigrationTeam, ProjectAttributesAccess


class MigrationTeamTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.email = "migration-team-admin@example.com"
        ProjectAttributesAccess.objects.create(
            email=self.email,
            migration_team=True,
        )
        self.headers = {"HTTP_X_USER_EMAIL": self.email}
        self.list_url = "/api/migration-team/"
        self.save_url = "/api/migration-team/data/"
        self.delete_url = "/api/migration-team/data/delete/"

    def test_list_create_and_update_rows(self):
        created = self.client.post(
            self.save_url,
            {"uniqueData": [{"role": "Manager", "email": "manager@example.com"}]},
            format="json",
            **self.headers,
        )
        record = MigrationTeam.objects.get(email="manager@example.com")
        updated = self.client.post(
            self.save_url,
            {"uniqueData": [{"id": record.id, "role": "Member", "email": "member@example.com"}]},
            format="json",
            **self.headers,
        )
        listed = self.client.get(self.list_url, **self.headers)

        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.data["created_count"], 1)
        self.assertEqual(updated.data["updated_count"], 1)
        self.assertEqual(listed.data["rows"], [{
            "id": record.id,
            "role": "Member",
            "email": "member@example.com",
        }])

    def test_save_rejects_unknown_role_and_invalid_or_missing_email(self):
        response = self.client.post(
            self.save_url,
            {
                "uniqueData": [
                    {"role": "MANAGER", "email": "valid@example.com"},
                    {"role": "member", "email": "legacy-role@example.com"},
                    {"role": "member", "email": "not-an-email"},
                    {"role": "Manager", "email": ""},
                ]
            },
            format="json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error_count"], 4)
        self.assertEqual(MigrationTeam.objects.count(), 0)

    def test_delete_saved_rows(self):
        first = MigrationTeam.objects.create(role="Manager", email="manager@example.com")
        second = MigrationTeam.objects.create(role="Member", email="member@example.com")

        response = self.client.delete(
            self.delete_url,
            {"removedIds": [first.id, second.id]},
            format="json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["deleted_count"], 2)
        self.assertEqual(MigrationTeam.objects.count(), 0)

    def test_table_permission_is_required(self):
        response = self.client.get(self.list_url, HTTP_X_USER_EMAIL="no-access@example.com")

        self.assertEqual(response.status_code, 403)

    def test_access_control_grid_includes_migration_team_permission(self):
        response = self.client.get(
            "/api/project-attributes-access/",
            HTTP_X_USER_EMAIL="local.dev@localhost",
        )

        row = next(item for item in response.data["rows"] if item["email"] == self.email)
        self.assertIn(
            {"key": "migration_team", "label": "Migration Team (Y/N)"},
            response.data["columns"],
        )
        self.assertEqual(row["migration_team"], "Y")
