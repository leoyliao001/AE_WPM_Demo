from datetime import date, datetime, timedelta

from django.db import migrations, models
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime


TIMELINE_WEEK_COUNT = 44
DEFAULT_CALENDAR_START_WEEK = 9


def _as_date(value):
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            return timezone.localtime(value).date()
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        parsed_datetime = parse_datetime(text)
        if parsed_datetime:
            if timezone.is_aware(parsed_datetime):
                return timezone.localtime(parsed_datetime).date()
            return parsed_datetime.date()
        return parse_date(text[:10])
    return None


def _week_index(created_at, actual_date):
    target_date = _as_date(actual_date)
    if not target_date:
        return None

    intake_date = _as_date(created_at)
    if intake_date:
        year, week, _weekday = intake_date.isocalendar()
        start_monday = date.fromisocalendar(year, week, 1) + timedelta(weeks=1)
    else:
        start_monday = date.fromisocalendar(
            date.today().year, DEFAULT_CALENDAR_START_WEEK, 1
        )

    delta_days = (target_date - start_monday).days
    index = delta_days // 7 + 1
    return max(1, min(TIMELINE_WEEK_COUNT, index))


def remove_completed_at(apps, schema_editor):
    ProjectGanttPlan = apps.get_model("api", "ProjectGanttPlan")
    plans = ProjectGanttPlan.objects.select_related("project").only(
        "id", "tasks", "project__created_at"
    )
    for plan in plans.iterator():
        tasks = plan.tasks if isinstance(plan.tasks, list) else []
        updated_tasks = []
        for task in tasks:
            if not isinstance(task, dict):
                continue
            updated = dict(task)
            completed_at = updated.pop("completedAt", None)
            legacy_completed_at = updated.pop("completed_at", None)
            completed_at = completed_at or legacy_completed_at
            actual = updated.get("actual")
            actual_is_valid = False
            if isinstance(actual, dict):
                try:
                    actual_start = int(actual["startWeek"])
                    actual_end = int(actual["endWeek"])
                    actual_is_valid = (
                        1 <= actual_start <= actual_end <= TIMELINE_WEEK_COUNT
                    )
                except (KeyError, TypeError, ValueError):
                    pass
            if not actual_is_valid and completed_at:
                completed_week = _week_index(plan.project.created_at, completed_at)
                if completed_week is not None:
                    plan_range = updated.get("plan")
                    try:
                        plan_start = max(
                            1,
                            min(
                                TIMELINE_WEEK_COUNT,
                                int(plan_range.get("startWeek")),
                            ),
                        )
                    except (AttributeError, TypeError, ValueError):
                        plan_start = completed_week
                    updated["actual"] = {
                        "startWeek": min(plan_start, completed_week),
                        "endWeek": completed_week,
                    }
            updated_tasks.append(updated)
        if updated_tasks != tasks:
            plan.tasks = updated_tasks
            plan.save(update_fields=["tasks"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0062_gantt_lifecycle_remove_standard"),
    ]

    operations = [
        migrations.RunPython(remove_completed_at, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="projectganttplan",
            name="tasks",
            field=models.JSONField(
                default=list,
                help_text=(
                    "[{id, name, lifecycleStage, plan:{startWeek,endWeek}, actual, "
                    "comments:[{id, at, text, updatedBy, fromPlan, toPlan}]}, ...]"
                ),
            ),
        ),
    ]
