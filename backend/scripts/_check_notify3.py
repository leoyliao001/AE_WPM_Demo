import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings

from api.models import MigrationIntakeSubmission
from api.services.migration_intake_notifications import (
    _manager_emails_for_submission,
    resolve_notification_recipients,
)

print("DB ENGINE:", settings.DATABASES["default"]["ENGINE"])
print("DB NAME:", settings.DATABASES["default"]["NAME"])
print("MIGRATION_INTAKE_NOTIFY_TO:", settings.MIGRATION_INTAKE_NOTIFY_TO)
print("DEFAULT_FROM_EMAIL:", settings.DEFAULT_FROM_EMAIL)
print("EMAIL_HOST_PASSWORD set:", bool(settings.EMAIL_HOST_PASSWORD))

s = MigrationIntakeSubmission.objects.filter(
    migration_request_id="WPM_PRJ_20260818831525"
).first()
print("SUBMISSION FOUND:", bool(s))
if s:
    print("  requestor:", repr(s.requestor))
    print("  region:", repr(s.region), "areas:", s.areas)
    print("  manager emails:", _manager_emails_for_submission(s))
    print("  recipients (no signed-in):", resolve_notification_recipients(s))
