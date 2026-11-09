from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api", "0056_opportunity_assessment_scope")]

    operations = [
        migrations.AddField(
            model_name="projectattributesaccess",
            name="user_name_list",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="UserNameList",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(db_index=True, max_length=255)),
                ("mail", models.CharField(blank=True, default="", max_length=255)),
            ],
            options={
                "db_table": "user_name_list",
                "ordering": ["display_name", "id"],
            },
        ),
    ]