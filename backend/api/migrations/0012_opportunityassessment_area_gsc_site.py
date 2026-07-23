from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0011_product_ownership_region_area"),
    ]

    operations = [
        migrations.AddField(
            model_name="opportunityassessment",
            name="area",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="opportunityassessment",
            name="gsc_site",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
    ]
