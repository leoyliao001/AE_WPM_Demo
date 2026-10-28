from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api", "0052_scope_shared_attachments")]

    operations = [
        migrations.AddField(
            model_name="scopestatement", name="migratable_fte",
            field=models.DecimalField(blank=True, null=True, max_digits=12, decimal_places=4),
        ),
        migrations.AddField(
            model_name="scopestatement", name="migratable_fte_confirmed",
            field=models.BooleanField(default=False),
        ),
    ]
