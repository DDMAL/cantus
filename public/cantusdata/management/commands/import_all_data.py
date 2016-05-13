from django.core.management.base import BaseCommand
from django.core.management import call_command
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio
from cantusdata.models.concordance import Concordance
from cantusdata.models.manuscript import Manuscript
from cantusdata.signals.solr_sync import solr_synchronizer


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        with solr_synchronizer.get_session():
            # Delete all of the data in the db
            self.stdout.write("Deleting all old chant data...")
            Chant.objects.all().delete()
            self.stdout.write("Old chants deleted.\nDeleting old folio data.")
            Folio.objects.all().delete()
            self.stdout.write("Old folios deleted.\nDeleting old manuscript data.")
            Manuscript.objects.all().delete()
            self.stdout.write("Old manuscripts deleted.\nDeleting old concordance data.")
            Concordance.objects.all().delete()
            self.stdout.write("Old concordances deleted.")

        # Load up the new data...
        call_command('import_manuscript_data', 'sources-export.csv', **kwargs)
        call_command('import_concordance_data', 'concordances', **kwargs)
        # St. Gallen 390 Chants
        call_command('import_chant_data', 'st-gallen-390-chants.csv', **kwargs)
        # St. Gallen 391 Chants
        call_command('import_chant_data', 'st-gallen-391-chants.csv', **kwargs)
        # Salzinnes
        call_command('import_chant_data', 'salzinnes-chants.csv', **kwargs)
