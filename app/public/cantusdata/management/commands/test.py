from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "The standard manage.py test command is disabled - use runtests.py instead"

    def handle(self, *args, **kwargs):
        raise CommandError(
            "Cannot run tests using manage.py test\n"
            "Use the runtests.py wrapper script instead to correctly configure the test environment"
        )
