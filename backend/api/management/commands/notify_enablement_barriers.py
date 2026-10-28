import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from api.models import AccessEnablement

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Email owners of overdue open Access & Enablement barriers, at most once per day. Schedule daily."

    def handle(self, *args, **options):
        today = timezone.localdate().isoformat()
        count = 0
        for key in AccessEnablement.objects.filter(status="draft").values_list("pk", flat=True):
            ids = [barrier["id"] for barrier in AccessEnablement.objects.get(pk=key).barriers]
            for barrier_id in ids:
                with transaction.atomic():
                    record = AccessEnablement.objects.select_for_update().select_related("project").get(pk=key)
                    barrier = next((item for item in record.barriers if item["id"] == barrier_id), None)
                    if record.status != "draft" or not barrier or barrier["status"] != "open" or barrier["targetDate"] >= today or barrier.get("lastNotifiedAt", "").startswith(today):
                        continue
                    base = getattr(settings, "DJANGO_PUBLIC_BASE_URL", "http://localhost:3002").rstrip("/")
                    try:
                        delivered = send_mail(
                            f"Overdue access barrier: {record.project.migration_request_id}",
                            f"{record.project.project_name}\n{barrier['systemName']}\nTarget: {barrier['targetDate']}\n"
                            f"{barrier['description']}\n{base}/migration-dashboard/{record.project_id}/access-enablement",
                            settings.DEFAULT_FROM_EMAIL, [barrier["owner"]], fail_silently=False,
                        )
                        if delivered != 1:
                            raise CommandError("Email backend did not accept the notification.")
                    except (OSError, CommandError) as exc:
                        logger.exception("Enablement barrier notification failed for %s", barrier["id"])
                        raise CommandError(f"Unable to notify {barrier['owner']}: {exc}") from exc
                    barrier["lastNotifiedAt"] = timezone.now().isoformat()
                    count += 1
                    record.revision += 1
                    record.audit_log = [*record.audit_log, {
                        "action": "overdue_notification", "by": "system", "at": timezone.now().isoformat(),
                        "revision": record.revision, "barrierIds": [barrier_id],
                    }]
                    record.save(update_fields=["barriers", "revision", "audit_log", "updated_at"])
        self.stdout.write(self.style.SUCCESS(f"{count} overdue barrier notifications accepted by the configured email backend."))
