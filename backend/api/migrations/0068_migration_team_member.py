from django.db import migrations, models


def capitalize_member_role(apps, schema_editor):
    MigrationTeam = apps.get_model("api", "MigrationTeam")
    MigrationTeam.objects.using(schema_editor.connection.alias).filter(role="member").update(
        role="Member"
    )


def restore_lowercase_member_role(apps, schema_editor):
    MigrationTeam = apps.get_model("api", "MigrationTeam")
    MigrationTeam.objects.using(schema_editor.connection.alias).filter(role="Member").update(
        role="member"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0066_migration_team"),
    ]

    operations = [
        migrations.RunPython(capitalize_member_role, restore_lowercase_member_role),
        migrations.AlterField(
            model_name="migrationteam",
            name="role",
            field=models.CharField(
                choices=[("Manager", "Manager"), ("Member", "Member")],
                max_length=16,
            ),
        ),
    ]
