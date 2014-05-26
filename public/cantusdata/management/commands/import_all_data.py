from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        call_command('import_manuscript_data', 'sources-export.csv', **kwargs)
        call_command('import_concordance_data', 'concordances', **kwargs)
        call_command('import_chant_data', 'exportchants.csv', **kwargs)
