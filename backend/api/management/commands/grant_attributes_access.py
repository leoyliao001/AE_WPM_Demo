"""Grant or update Project Attributes Database access for an SSO email.

Usage:
  python manage.py grant_attributes_access user@example.com --super-admin
  python manage.py grant_attributes_access user@example.com --tables fpo_mapping bpm_rofo
"""

from django.core.management.base import BaseCommand, CommandError

from api.models import ProjectAttributesAccess
from api.permissions.attributes_access import TABLE_KEYS, normalize_email


class Command(BaseCommand):
    help = "Grant or update Project Attributes Database access for an SSO email."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="SSO email to grant access to.")
        parser.add_argument(
            "--super-admin",
            action="store_true",
            help="Grant super admin (access to every table).",
        )
        parser.add_argument(
            "--tables",
            nargs="*",
            choices=TABLE_KEYS,
            default=[],
            help="Specific table keys to grant (ignored if --super-admin is set).",
        )

    def handle(self, *args, **options):
        email = normalize_email(options["email"])
        if not email:
            raise CommandError("Email is required.")

        defaults = {key: False for key in TABLE_KEYS}
        for key in options["tables"]:
            defaults[key] = True
        defaults["is_super_admin"] = options["super_admin"]

        row, created = ProjectAttributesAccess.objects.update_or_create(
            email=email, defaults=defaults
        )
        action = "Created" if created else "Updated"
        role = "super_admin" if row.is_super_admin else f"tables={options['tables']}"
        self.stdout.write(self.style.SUCCESS(f"{action} access for {email} ({role})."))
