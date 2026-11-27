from django.db import migrations


def remove_weekly_comments(apps, schema_editor):
    BaselineKpiRecord = apps.get_model("api", "BaselineKpiRecord")
    database = schema_editor.connection.alias
    records = BaselineKpiRecord.objects.using(database).all().iterator()
    for record in records:
        state = record.state
        if not isinstance(state, dict):
            continue
        cohorts = state.get("cohorts")
        if not isinstance(cohorts, dict):
            continue

        changed = False
        for cohort in cohorts.values():
            if not isinstance(cohort, dict):
                continue
            kpis = cohort.get("kpis")
            if not isinstance(kpis, list):
                continue
            for kpi in kpis:
                if isinstance(kpi, dict) and "comments" in kpi:
                    del kpi["comments"]
                    changed = True

        if changed:
            BaselineKpiRecord.objects.using(database).filter(pk=record.pk).update(state=state)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0081_baselinekpirecord"),
    ]

    operations = [
        migrations.RunPython(remove_weekly_comments, migrations.RunPython.noop),
    ]
