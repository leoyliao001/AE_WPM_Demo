from django.test import TestCase
from rest_framework.test import APIClient

from api.models import ProjectAttributesAccess, UserNameList


class UserNameListTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_email = "user-list-admin@example.com"
        ProjectAttributesAccess.objects.create(
            email=self.admin_email,
            user_name_list=True,
        )
        self.headers = {"HTTP_X_USER_EMAIL": self.admin_email}
        self.search_url = "/api/user-name-list/"
        self.save_url = "/api/user-name-list/data/"

    def test_search_requires_filter_and_matches_name_or_mail_fragments(self):
        UserNameList.objects.create(display_name="Alexandra Lee", mail="alex@example.com")
        UserNameList.objects.create(display_name="Morgan Reed", mail="morgan@example.com")

        missing_filter = self.client.get(self.search_url, **self.headers)
        matching_name = self.client.get(self.search_url, {"display_name": "xand"}, **self.headers)
        matching_mail = self.client.get(self.search_url, {"mail": "morgan@"}, **self.headers)

        self.assertEqual(missing_filter.status_code, 400)
        self.assertEqual(matching_name.data["count"], 1)
        self.assertEqual(matching_name.data["rows"][0]["display_name"], "Alexandra Lee")
        self.assertEqual(matching_mail.data["rows"][0]["display_name"], "Morgan Reed")

    def test_save_inserts_and_updates_records(self):
        created = self.client.post(
            self.save_url,
            {"uniqueData": [{"display_name": "Jamie Park", "mail": "jamie@example.com"}]},
            format="json",
            **self.headers,
        )
        record = UserNameList.objects.get(mail="jamie@example.com")
        updated = self.client.post(
            self.save_url,
            {"uniqueData": [{"id": record.id, "display_name": "Jamie P.", "mail": "jp@example.com"}]},
            format="json",
            **self.headers,
        )
        record.refresh_from_db()

        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.data["created_count"], 1)
        self.assertEqual(updated.data["updated_count"], 1)
        self.assertEqual(record.display_name, "Jamie P.")
        self.assertEqual(record.mail, "jp@example.com")

    def test_delete_removes_selected_records(self):
        first = UserNameList.objects.create(display_name="Jamie Park", mail="jamie@example.com")
        second = UserNameList.objects.create(display_name="Taylor Reed", mail="taylor@example.com")

        response = self.client.delete(
            "/api/user-name-list/data/delete/",
            {"removedIds": [first.id, second.id]},
            format="json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["deleted_count"], 2)
        self.assertFalse(UserNameList.objects.filter(pk__in=[first.id, second.id]).exists())

    def test_delete_rejects_invalid_ids_and_oversized_batches(self):
        invalid = self.client.delete(
            "/api/user-name-list/data/delete/",
            {"removedIds": ["not-an-id"]},
            format="json",
            **self.headers,
        )
        oversized = self.client.delete(
            "/api/user-name-list/data/delete/",
            {"removedIds": list(range(1, 502))},
            format="json",
            **self.headers,
        )

        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(oversized.status_code, 400)

    def test_table_permission_is_independent_and_required_for_search_and_save(self):
        UserNameList.objects.create(display_name="Casey Quinn", mail="casey@example.com")
        for method, url, payload in (
            ("get", self.search_url, {"display_name": "Casey"}),
            ("post", self.save_url, {"uniqueData": [{"display_name": "New Person"}]}),
            ("delete", "/api/user-name-list/data/delete/", {"removedIds": [1]}),
        ):
            response = getattr(self.client, method)(url, payload, format="json")
            self.assertEqual(response.status_code, 401)

        ProjectAttributesAccess.objects.create(email="other@example.com", access_control=True)
        for method, url, payload in (
            ("get", self.search_url, {"display_name": "Casey"}),
            ("post", self.save_url, {"uniqueData": [{"display_name": "New Person"}]}),
            ("delete", "/api/user-name-list/data/delete/", {"removedIds": [1]}),
        ):
            response = getattr(self.client, method)(
                url,
                payload,
                format="json",
                HTTP_X_USER_EMAIL="other@example.com",
            )
            self.assertEqual(response.status_code, 403)

    def test_access_control_grid_includes_user_name_list_permission(self):
        response = self.client.get(
            "/api/project-attributes-access/",
            HTTP_X_USER_EMAIL="local.dev@localhost",
        )

        row = next(item for item in response.data["rows"] if item["email"] == self.admin_email)
        self.assertIn(
            {"key": "user_name_list", "label": "User Name List (Y/N)"},
            response.data["columns"],
        )
        self.assertEqual(row["user_name_list"], "Y")