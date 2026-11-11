from datetime import datetime
from types import SimpleNamespace

from django.test import SimpleTestCase

from api.views.project_gantt import (
    DEFAULT_LIFECYCLE_STAGE_BY_TASK_ID,
    TEMPLATE_TASKS,
    _normalize_tasks,
    _serialize_plan,
    build_template_tasks,
    merge_gantt_tasks_with_template,
)
from api.views.project_gantt_attributes import _normalize_task_rows


class ProjectGanttTaskSchemaTests(SimpleTestCase):
    def test_template_tasks_have_lifecycle_stages_and_no_standard_ranges(self):
        tasks = build_template_tasks()

        self.assertEqual(len(tasks), len(TEMPLATE_TASKS))
        self.assertTrue(all(task["lifecycleStage"] for task in tasks))
        self.assertTrue(all("standard" not in task for task in tasks))
        self.assertTrue(all(task["plan"] is None for task in tasks))

    def test_old_standard_data_is_not_returned_and_template_stage_is_added(self):
        tasks, _template = merge_gantt_tasks_with_template(
            [
                {
                    "id": "business-case",
                    "name": "Business Case (Memo)",
                    "standard": {"startWeek": 1, "endWeek": 2},
                    "plan": None,
                }
            ]
        )

        self.assertEqual(tasks[0]["lifecycleStage"], "initiate")
        self.assertIsNone(tasks[0]["plan"])
        self.assertNotIn("standard", tasks[0])

    def test_task_normalization_persists_lifecycle_stage_without_standard(self):
        tasks = _normalize_tasks(
            [
                {
                    "id": "knowledge-transfer",
                    "name": "Knowledge Transfer",
                    "standard": {"startWeek": 3, "endWeek": 4},
                    "plan": None,
                }
            ]
        )

        self.assertEqual(
            tasks[0]["lifecycleStage"],
            DEFAULT_LIFECYCLE_STAGE_BY_TASK_ID["knowledge-transfer"],
        )
        self.assertNotIn("standard", tasks[0])

    def test_task_normalization_rejects_unknown_lifecycle_stage(self):
        with self.assertRaisesRegex(ValueError, "Invalid lifecycle stage"):
            _normalize_tasks(
                [
                    {
                        "id": "custom-task",
                        "name": "Custom task",
                        "lifecycleStage": "unknown",
                    }
                ]
            )

    def test_attributes_task_normalization_preserves_lifecycle_stage(self):
        tasks = _normalize_task_rows(
            [
                {
                    "task_id": "custom-close-task",
                    "name": "Custom close task",
                    "lifecycleStage": "close_realize_value",
                }
            ]
        )

        self.assertEqual(tasks[0]["lifecycleStage"], "close_realize_value")
        self.assertNotIn("standard", tasks[0])

    def test_gantt_response_does_not_expose_removed_summary_fields(self):
        project = SimpleNamespace(
            id=5,
            migration_request_id="WPM_TEST",
            created_at=datetime(2026, 1, 5),
            business_case_submission_date=None,
        )
        plan = SimpleNamespace(tasks=[], updated_at=None)

        response = _serialize_plan(plan, project)

        self.assertNotIn("region", response)
        self.assertNotIn("areas", response)
        self.assertNotIn("meta", response)
        self.assertEqual(
            [bar_type["id"] for bar_type in response["barTypes"]],
            ["plan", "actual"],
        )
