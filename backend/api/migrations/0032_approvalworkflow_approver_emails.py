from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api", "0031_approvalworkflow_bpm_status")]

    operations = [
        migrations.AddField(model_name="approvalworkflow", name="area_head_approved_by", field=models.CharField(blank=True, default="", max_length=255)),
        migrations.AddField(model_name="approvalworkflow", name="pmo_approved_by", field=models.CharField(blank=True, default="", max_length=255)),
        migrations.AddField(model_name="approvalworkflow", name="bpm_approved_by", field=models.CharField(blank=True, default="", max_length=255)),
        migrations.AddField(model_name="approvalworkflow", name="fbp_approved_by", field=models.CharField(blank=True, default="", max_length=255)),
        migrations.AddField(model_name="approvalworkflow", name="elt_approved_by", field=models.CharField(blank=True, default="", max_length=255)),
        migrations.AddField(model_name="approvalworkflow", name="gsc_head_approved_by", field=models.CharField(blank=True, default="", max_length=255)),
    ]