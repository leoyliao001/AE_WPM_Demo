from django.db import migrations, models


SUPER_ADMIN_EMAILS = [
    "local.dev@localhost",
    "leo.y.liao@lns.maersk.com",
    "kirandaware@maersk.com",
    "sampath.kumar.v@maersk.com",
]


def seed_super_admins(apps, schema_editor):
    ProjectAttributesAccess = apps.get_model("api", "ProjectAttributesAccess")
    for email in SUPER_ADMIN_EMAILS:
        ProjectAttributesAccess.objects.update_or_create(
            email=email.lower(),
            defaults={
                "is_super_admin": True,
                "fpo_mapping": True,
                "product_ownership": True,
                "gsc_site_mapping": True,
                "access_control": True,
            },
        )


def unseed_super_admins(apps, schema_editor):
    ProjectAttributesAccess = apps.get_model("api", "ProjectAttributesAccess")
    ProjectAttributesAccess.objects.filter(email__in=SUPER_ADMIN_EMAILS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0012_opportunityassessment_area_gsc_site"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectAttributesAccess",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.CharField(db_index=True, max_length=255, unique=True)),
                ("is_super_admin", models.BooleanField(default=False)),
                ("fpo_mapping", models.BooleanField(default=False)),
                ("product_ownership", models.BooleanField(default=False)),
                ("gsc_site_mapping", models.BooleanField(default=False)),
                ("access_control", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "project_attributes_access",
                "ordering": ["email"],
            },
        ),
        migrations.RunPython(seed_super_admins, unseed_super_admins),
    ]
