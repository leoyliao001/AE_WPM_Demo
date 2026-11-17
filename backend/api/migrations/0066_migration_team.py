from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0061_fpocataloguerequest_batch_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectattributesaccess",
            name="migration_team",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="MigrationTeam",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("Manager", "Manager"), ("member", "member")], max_length=16)),
                ("email", models.EmailField(max_length=254)),
            ],
            options={
                "db_table": "migration_team",
                "ordering": ["id"],
            },
        ),
    ]
