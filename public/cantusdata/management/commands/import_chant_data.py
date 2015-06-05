import csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant
from cantusdata.models.concordance import Concordance
from cantusdata.models import Folio
from cantusdata.helpers import expandr
from cantusdata.helpers.signal_wrangler import signal_receivers_disconnected


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        """
        Run "python manage.py import_chant_data filename.csv" to import a chant
        file into the db.  filename.csv must exist in /public/data_dumps/.
        """
        if args and args[0]:
            csv_file_name = args[0]
        else:
            raise ValueError("Please provide a file name!")

        importer = ChantImporter(self.stdout)

        # Load in the csv file.  This is a massive list of dictionaries.
        with open("data_dumps/" + str(csv_file_name)) as csv_file:
            csv_content = csv.DictReader(csv_file)
            self.stdout.write("Starting chant import process.")

            # Create chants and save them
            for index, row in enumerate(csv_content):
                importer.add_chant(row)

                # Tracking
                if (index % 100) == 0:
                    self.stdout.write(u"{0} chants processed for import.".format(index))

        self.stdout.write(u"Preparing to import {0} chants into the database".format(index))

        importer.save()

        self.stdout.write(u"Indexing chants in Solr...")

        importer.update_solr()

        self.stdout.write(
            u"Successfully imported {0} chants into database.".format(index))


class ChantImporter:
    def __init__(self, stdout):
        self.stdout = stdout

        # Map siglum to manuscript model
        self._manuscript_cache = {}

        self.chants_and_concordances = []
        self.new_folios = []

        # These are set after adding is complete
        self.affected_folios = self.affected_manuscripts = None

        self.folio_registry = set()

        # Use position expander object to get correct positions
        self.position_expander = expandr.PositionExpander()

    def add_chant(self, row):
        """Get a chant object to save to the database.

        Prepare a folio object to add if necessary.
        """

        # Get the corresponding manuscript
        manuscript = self.get_manuscript(row['Siglum'])

        # Throw exception if no corresponding manuscript
        if not manuscript:
            raise ValueError(u"Manuscript with Siglum={0} does not exist!"
                             .format(slugify(unicode(row["Siglum"]))))

        chant = Chant()
        chant.marginalia = row["Marginalia"].strip().decode('utf-8')
        chant.sequence = row["Sequence"].strip().decode('utf-8')
        chant.cantus_id = row["Cantus ID"].strip().decode('utf-8')
        chant.feast = row["Feast"].strip().decode('utf-8')
        chant.office = expandr.expand_office(row["Office"].strip()).decode('utf-8')
        chant.genre = expandr.expand_genre(row["Genre"].strip()).decode('utf-8')
        chant.mode = expandr.expand_mode(row["Mode"].strip()).decode('utf-8')
        chant.differentia = expandr.expand_differentia(row["Differentia"].strip()).decode('utf-8')
        chant.finalis = row["Finalis"].strip().decode('utf-8')
        chant.incipit = row["Incipit"].strip().decode('utf-8')
        chant.full_text = row["Fulltext"].strip().decode('utf-8')
        chant.volpiano = row["Volpiano"].strip().decode('utf-8')
        chant.lit_position = self.position_expander.get_text(
            row["Office"].strip(), row["Genre"].strip(),
            row["Position"].strip()).decode('utf-8')
        chant.manuscript = manuscript

        folio_code = slugify(row["Folio"].decode("utf-8"))

        # See if this folio already exists or is set to be created
        if (folio_code, manuscript.pk) not in self.folio_registry:
            try:
                folio = Folio.objects.get(number=folio_code, manuscript=manuscript)
            except Folio.DoesNotExist:
                # If the folio doesn't exist, prepare to create it
                self.add_folio(folio_code, manuscript)

        chant.folio = folio

        # Concordances
        concordances = []
        for c in list(row["Concordances"]):
            matching_concordance = Concordance.objects.filter(letter_code=c)
            if matching_concordance:
                concordances.append(matching_concordance[0])

        self.chants_and_concordances.append((chant, concordances))

    def add_folio(self, folio_code, manuscript):
        folio = Folio()
        folio.number = folio_code
        folio.manuscript = manuscript

        self.new_folios.append(folio)
        self.folio_registry.add((folio_code, manuscript.pk))

    def get_manuscript(self, siglum):
        try:
            return self._manuscript_cache[siglum]
        except KeyError:
            manuscript = self._manuscript_cache[siglum] = Manuscript.objects.get(siglum=siglum)
            return manuscript

    def save(self):
        # Disconnect the post_save signals so that we don't update Solr yet
        # Note that the bulk_create methods wouldn't fire the post_save
        # receivers anyway
        receivers = [
            'cantusdata_folio_solr_add',
            'cantusdata_manuscript_solr_add',
            'cantusdata_manuscript_update_chant_count'
        ]

        with signal_receivers_disconnected(*receivers):
            for folio in self.new_folios:
                folio.save()

            for index, (chant, concordances) in enumerate(self.chants_and_concordances):
                chant.save()

                # Now that the chant is saved, add the concordances
                if concordances:
                    chant.concordances.add(*concordances)

                # Tracking
                if (index % 100) == 0:
                    self.stdout.write(u"{0} chants saved in the Django database.".format(index))

            # Get all the unique folios and manuscripts affected by adding the chants
            chants = [pair[0] for pair in self.chants_and_concordances]
            self.affected_folios = dict((chant.folio.pk, chant.folio)
                                        for chant in chants).values()

            self.affected_manuscripts = dict((folio.manuscript.pk, folio.manuscript)
                                             for folio in self.affected_folios).values()

            # Update the chant counts
            for folio in self.affected_folios:
                folio.update_chant_count()

            for manuscript in self.affected_manuscripts:
                manuscript.update_chant_count()

    def update_solr(self):
        import solr
        from cantusdata import settings

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        for (chant, _) in self.chants_and_concordances:
            chant.add_to_solr(solrconn)

        for folio in self.affected_folios:
            folio.delete_from_solr(solrconn)
            folio.add_to_solr(solrconn)

        for manuscript in self.affected_manuscripts:
            manuscript.delete_from_solr(solrconn)
            manuscript.add_to_solr(solrconn)

        solrconn.commit()
