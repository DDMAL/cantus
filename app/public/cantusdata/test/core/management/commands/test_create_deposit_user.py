from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework.authtoken.models import Token

User = get_user_model()


class CreateDepositUserTestCase(TestCase):
    """
    The command mints an API token, so which account it is willing to mint one
    for is the whole security question: a token authenticates as that account
    for every token-authenticated endpoint, now and in future.
    """

    def run_command(self, **options: object) -> str:
        out = StringIO()
        call_command("create_deposit_user", stdout=out, **options)
        return out.getvalue()

    # --- the account it is meant to create ------------------------------

    def test_creates_a_service_account_with_a_token(self) -> None:
        output = self.run_command()
        user = User.objects.get(username="mothra")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(
            set(user.get_all_permissions()),
            {"cantusdata.add_meisubmission", "cantusdata.view_meisubmission"},
        )
        self.assertIn(Token.objects.get(user=user).key, output)

    def test_re_running_keeps_the_same_token(self) -> None:
        self.run_command()
        original = Token.objects.get(user__username="mothra").key
        self.run_command()
        self.assertEqual(Token.objects.get(user__username="mothra").key, original)

    def test_rotating_replaces_the_token(self) -> None:
        self.run_command()
        original = Token.objects.get(user__username="mothra").key
        self.run_command(rotate_token=True)
        self.assertNotEqual(Token.objects.get(user__username="mothra").key, original)

    # --- accounts it must refuse ----------------------------------------

    def assert_refused(self, user: object, fragment: str) -> None:
        with self.assertRaises(CommandError) as raised:
            self.run_command(username=user.get_username())
        self.assertIn(fragment, str(raised.exception))
        # Nothing granted, no credential issued.
        self.assertFalse(Token.objects.filter(user=user).exists())
        self.assertEqual(user.user_permissions.count(), 0)

    def test_refuses_a_superuser(self) -> None:
        """The typo that would otherwise print a bearer token for an admin."""
        admin = User.objects.create_superuser(
            username="dchiller", email="", password="hahaha"
        )
        self.assert_refused(admin, "is a superuser")

    def test_refuses_a_staff_account(self) -> None:
        reviewer = User.objects.create_user(
            username="reviewer", password="hahaha", is_staff=True
        )
        self.assert_refused(reviewer, "has admin access")

    def test_refuses_an_ordinary_person(self) -> None:
        """
        The likeliest accident: a plain reader account is neither staff nor
        privileged, so only the password distinguishes it from a service account.
        """
        person = User.objects.create_user(username="asadra", password="hahaha")
        self.assertFalse(person.is_staff)
        self.assertFalse(person.get_all_permissions())
        self.assert_refused(person, "belongs to a person")

    def test_refuses_an_account_holding_unrelated_permissions(self) -> None:
        holder = User.objects.create_user(username="importer")
        holder.set_unusable_password()
        holder.save()
        holder.user_permissions.add(
            Permission.objects.get(
                codename="change_manuscript", content_type__app_label="cantusdata"
            )
        )
        with self.assertRaises(CommandError) as raised:
            self.run_command(username="importer")
        self.assertIn("unrelated permissions", str(raised.exception))
        self.assertIn("cantusdata.change_manuscript", str(raised.exception))
        self.assertFalse(Token.objects.filter(user=holder).exists())

    def test_permissions_from_a_group_count_too(self) -> None:
        """
        Checked with get_all_permissions rather than the user_permissions
        relation, or an account privileged only through a group would slip past.
        """
        group = Group.objects.create(name="editors")
        group.permissions.add(
            Permission.objects.get(
                codename="change_manuscript", content_type__app_label="cantusdata"
            )
        )
        member = User.objects.create_user(username="via-group")
        member.set_unusable_password()
        member.save()
        member.groups.add(group)
        with self.assertRaises(CommandError) as raised:
            self.run_command(username="via-group")
        self.assertIn("unrelated permissions", str(raised.exception))

    def test_a_refused_account_is_left_untouched(self) -> None:
        admin = User.objects.create_superuser(
            username="dchiller", email="", password="hahaha"
        )
        with self.assertRaises(CommandError):
            self.run_command(username="dchiller")
        admin.refresh_from_db()
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.has_usable_password())
        self.assertEqual(admin.user_permissions.count(), 0)
        self.assertFalse(Token.objects.filter(user=admin).exists())

    def test_an_existing_service_account_is_still_accepted(self) -> None:
        """The guard must not break the re-run the command advertises."""
        self.run_command()
        output = self.run_command()
        self.assertIn("already exists", output)
