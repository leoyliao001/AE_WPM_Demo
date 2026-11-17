from django.db import migrations, models


def seed_migration_team_members(apps, schema_editor):
    database = schema_editor.connection.alias
    MigrationTeam = apps.get_model("api", "MigrationTeam")
    StakeholderRegistration = apps.get_model("api", "StakeholderRegistration")
    UserNameList = apps.get_model("api", "UserNameList")

    defaults = []
    seen_emails = set()
    for source in MigrationTeam.objects.using(database).filter(role="Member").order_by("id"):
        email = str(source.email or "").strip().lower()
        if not email or email in seen_emails:
            continue
        seen_emails.add(email)
        full_name = (
            UserNameList.objects.using(database)
            .filter(mail__iexact=email)
            .values_list("display_name", flat=True)
            .first()
        ) or email
        defaults.append({
            "id": f"migration-team-{source.pk}",
            "fullName": full_name[:120],
            "email": email[:254],
            "title": "",
            "organization": "",
            "location": "",
        })

    for registration in StakeholderRegistration.objects.using(database).all().iterator():
        members = registration.team_members if isinstance(registration.team_members, list) else []
        existing_emails = {
            str(person.get("email") or "").strip().lower()
            for person in members
            if isinstance(person, dict)
        }
        for person in defaults:
            email = person["email"]
            if email not in existing_emails:
                members.append(dict(person))
                existing_emails.add(email)
        if len(members) > 100:
            raise RuntimeError(
                f"Project Team for registration {registration.pk} exceeds the 100-member limit after default members are added."
            )
        registration.team_members = members
        registration.migration_team_defaults_applied = True
        registration.save(
            using=database,
            update_fields=["team_members", "migration_team_defaults_applied"],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0068_migration_team_member"),
    ]

    operations = [
        migrations.AddField(
            model_name="stakeholderregistration",
            name="migration_team_defaults_applied",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(seed_migration_team_members, migrations.RunPython.noop),
    ]
