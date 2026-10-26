from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0044_projectattributesaccess_scope_statement"),
    ]

    operations = [
        migrations.AlterField(
            model_name="projectattributesaccess",
            name="scope_statement",
            field=models.BooleanField(default=False),
        ),
    ]