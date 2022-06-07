from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

class Command(BaseCommand):
    """
    Completely clears the django_session table. Runs `TRUNCATE django_session` against the
    database. 

    This is useful when building the app container with a database that is not a fresh build
    to avoid a 'Session data corrupted' warning.
    """
    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE django_session;")
