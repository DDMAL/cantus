from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandParser
from rest_framework.authtoken.models import Token

DEFAULT_USERNAME = "mothra"

# What a depositing application is allowed to do: file submissions and read
# back their status. Reviewing is a separate, human act in the admin.
DEPOSIT_PERMISSIONS = ["add_meisubmission", "view_meisubmission"]


class Command(BaseCommand):
    help = (
        "Creates (or updates) the service account an external OMR pipeline uses to "
        "deposit MEI, grants it the deposit permissions, and prints its API token. "
        "Safe to re-run: an existing account keeps its token unless --rotate-token "
        "is given."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--username",
            type=str,
            default=DEFAULT_USERNAME,
            help=f"Username for the service account. Defaults to '{DEFAULT_USERNAME}'.",
        )
        parser.add_argument(
            "--rotate-token",
            action="store_true",
            help=(
                "Replace the account's existing token with a new one. The old token "
                "stops working immediately, so deploy the new one to the depositing "
                "application first, or keep a second service account in reserve for "
                "overlapping rotation."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        username = options["username"]
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"is_staff": False, "is_superuser": False},
        )
        if created:
            # No usable password: this account authenticates by token only, and
            # must not be able to log in to the admin.
            user.set_unusable_password()
            user.save()
            self.stdout.write(f"Created service account '{username}'.")
        else:
            self.stdout.write(f"Service account '{username}' already exists.")

        permissions = Permission.objects.filter(
            codename__in=DEPOSIT_PERMISSIONS,
            content_type__app_label="cantusdata",
        )
        missing = set(DEPOSIT_PERMISSIONS) - {p.codename for p in permissions}
        if missing:
            raise RuntimeError(
                f"Permissions not found: {sorted(missing)}. Run migrations first."
            )
        user.user_permissions.add(*permissions)
        self.stdout.write(f"Granted: {', '.join(DEPOSIT_PERMISSIONS)}.")

        if options["rotate_token"]:
            Token.objects.filter(user=user).delete()
        token, token_created = Token.objects.get_or_create(user=user)
        self.stdout.write(
            self.style.SUCCESS(
                f"{'New' if token_created else 'Existing'} token for '{username}': "
                f"{token.key}"
            )
        )
        self.stdout.write(
            "Send it as an 'Authorization: Token <key>' header to "
            "/api/mei-submissions/."
        )
