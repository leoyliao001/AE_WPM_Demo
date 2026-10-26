from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0043_scope_statement"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectattributesaccess",
            name="scope_statement",
            field=models.BooleanField(default=True),
        ),
    ]