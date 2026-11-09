from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0057_people_consultation_compliance"),
    ]

    operations = [
        migrations.AddField(
            model_name="opportunityassessment",
            name="system",
            field=models.TextField(blank=True, default=""),
        ),
    ]