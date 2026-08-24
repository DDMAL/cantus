from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError, CommandParser
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

    def reject_unless_service_account(self, user: Any) -> None:
        """
        Refuse to issue a deposit token for anything but a service account.

        The checks are what distinguishes the account this command creates from
        one belonging to a person: no admin access, no permissions beyond the
        deposit set, and no usable password. The password check is the one that
        catches the likeliest accident -- an ordinary reader account, which is
        non-staff and unprivileged and would otherwise pass.

        Permissions are read with get_all_permissions() rather than the
        user_permissions relation so that anything conferred by a group counts
        too.
        """
        problems = []
        if user.is_superuser:
            problems.append("is a superuser")
        if user.is_staff:
            problems.append("has admin access")
        if user.has_usable_password():
            problems.append("has a password, so it belongs to a person")

        if not user.is_superuser:
            # Skipped for a superuser, whose get_all_permissions() is every
            # permission there is -- already reported above, and not worth
            # enumerating into the error.
            expected = {f"cantusdata.{codename}" for codename in DEPOSIT_PERMISSIONS}
            extra = sorted(set(user.get_all_permissions()) - expected)
            if extra:
                problems.append(f"holds unrelated permissions ({', '.join(extra)})")

        if problems:
            raise CommandError(
                f"'{user.get_username()}' {' and '.join(problems)}, so it is not a "
                "deposit service account. Refusing to grant it deposit permissions "
                "or issue it an API token -- a token authenticates as this account, "
                "and nothing here has been changed. Pass --username to name a "
                "dedicated service account instead."
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
            # An existing account is only safe to reuse if it is already a
            # service account. Otherwise this command would grant a human --
            # or an admin -- the deposit permissions and print a bearer token
            # for them, which is a mistake a single typo in --username is enough
            # to make, and one that prints a durable credential to the terminal
            # rather than failing.
            self.reject_unless_service_account(user)
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
