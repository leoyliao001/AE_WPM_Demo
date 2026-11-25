from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0073_learningcapabilityrecord"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="migrationintakesubmission",
            name="risks",
        ),
    ]
