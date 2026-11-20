from django.test import TestCase

from api.models import MigrationIntakeSubmission, ProductOwnership
from api.services.migration_dashboard import serialize_project_overview


class MigrationPortfolioOverviewTests(TestCase):
    def test_overview_exposes_intake_dates_and_resolves_manager_from_area_ownership(self):
        project = MigrationIntakeSubmission.objects.create(
            migration_request_id="PORTFOLIO-TEST",
            requested_date="20 Nov 2026",
            requestor="requestor@example.com",
            project_name="Portfolio project",
            migration_type="1:1 Transfer",
            migration_type_value="1:1-transfer",
            region="APA",
            areas=["SEA"],
            function_name="Operations",
            proposed_scope="Portfolio API test",
            fte_number="12",
            target_start_date="2026-12-01",
            target_end_date="2027-02-01",
        )
        ProductOwnership.objects.create(
            region="APA",
            area="SEA",
            migration_manager="Portfolio Manager",
        )

        result = serialize_project_overview(project)

        self.assertEqual(result["owner"], "Portfolio Manager")
        self.assertEqual(result["targetStartDate"], "2026-12-01")
        self.assertEqual(result["targetEndDate"], "2027-02-01")
