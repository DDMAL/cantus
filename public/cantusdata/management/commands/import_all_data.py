from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import solr

class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        # create a new model here.