from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api", "0060_opportunityassessment_system")]

    operations = [
        migrations.AddField(
            model_name="fpocataloguerequest",
            name="batch_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
    ]
