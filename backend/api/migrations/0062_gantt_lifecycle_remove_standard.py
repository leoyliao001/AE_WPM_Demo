from django.db import migrations, models


DEFAULT_STAGE_BY_TASK_ID = {
    "business-case": "initiate",
    "fbp-approval": "initiate",
    "functional-head": "initiate",
    "elt-approval": "initiate",
    "gsc-head": "initiate",
    "opportunity-assessment": "initiate",
    "pid-approval": "initiate",
    "hiring-request": "initiate",
    "resource-mobilization": "execute",
    "neo-training": "execute",
    "knowledge-transfer": "plan",
    "volume-transfer": "execute",
    "hypercare": "monitor_control",
    "hypercare-exit": "monitor_control",
    "sign-off": "close_realize_value",
    "capacity-release": "close_realize_value",
}
VALID_STAGES = {
    "initiate",
    "plan",
    "execute",
    "monitor_control",
    "close_realize_value",
}


def remove_standard_and_classify_tasks(apps, schema_editor):
    ProjectGanttPlan = apps.get_model("api", "ProjectGanttPlan")
    for plan in ProjectGanttPlan.objects.only("id", "tasks").iterator():
        tasks = plan.tasks if isinstance(plan.tasks, list) else []
        updated_tasks = []
        for task in tasks:
            if not isinstance(task, dict):
                continue
            updated = {key: value for key, value in task.items() if key != "standard"}
            stage = str(updated.get("lifecycleStage") or "").strip()
            if stage not in VALID_STAGES:
                task_id = str(updated.get("id") or "").strip()
                stage = DEFAULT_STAGE_BY_TASK_ID.get(task_id, "initiate")
            updated["lifecycleStage"] = stage
            updated_tasks.append(updated)
        if updated_tasks != tasks:
            plan.tasks = updated_tasks
            plan.save(update_fields=["tasks"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0061_fpocataloguerequest_batch_id"),
    ]

    operations = [
        migrations.RunPython(
            remove_standard_and_classify_tasks,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="projectganttplan",
            name="tasks",
            field=models.JSONField(
                default=list,
                help_text=(
                    "[{id, name, lifecycleStage, plan:{startWeek,endWeek}, actual, "
                    "completedAt, comments:[{id, at, text, updatedBy, fromPlan, toPlan}]}, ...]"
                ),
            ),
        ),
        migrations.AlterField(
            model_name="projectganttplan",
            name="meta",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Project Gantt Attributes metadata.",
            ),
        ),
    ]
