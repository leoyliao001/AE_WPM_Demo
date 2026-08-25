from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0027_approval_input"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectattributesaccess",
            name="input_for_approval",
            field=models.BooleanField(default=False),
        ),
    ]
