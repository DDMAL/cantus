import csv
from optparse import make_option

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant
from cantusdata.models.concordance import Concordance
from cantusdata.models import Folio
from cantusdata.helpers import expandr
from cantusdata.helpers.signal_wrangler import signal_receivers_disconnected


class Command(BaseCommand):
    args = 'filename.csv'

    option_list = BaseCommand.option_list + (
        make_option('--delete-existing',
                    action='store_true',
                    dest='delete_existing',
                    default=False,
                    help='Delete existing chant records for all manuscripts touched by the import'),

        make_option('--no-save',
                    action='store_true',
                    dest='no_save',
                    default=False,
                    help=("Process but don't save the new chants (useful for testing). "
                          "NOTE: This does NOT affect the --delete-existing flag."))
    )

    def handle(self, *args, **options):
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

        if options['delete_existing']:
            self.stdout.write(u"Deleting existing chants for the affected manuscripts")
            importer.delete_existing_chants()

        if options['no_save']:
            self.stdout.write(u"Found {0} chants to import. Exiting.".format(index))
            return

        self.stdout.write(u"Preparing to import {0} chants into the database".format(index))

        # Save the new chants
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

        self.new_chant_info = []
        self.new_folios = []

        # These are set after adding is complete
        self._affected_entries_determined = False
        self.affected_folios = self.affected_manuscripts = None

        self.folio_registry = set()

        # Use position expander object to get correct positions
        self.position_expander = expandr.PositionExpander()

    def add_chant(self, row):
        """Get a chant object to save to the database.

        Prepare a folio object to add if necessary.
        """

        if self._affected_entries_determined:
            raise ValueError('cannot add new chants: affected values have already been found')

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
                folio = None

        else:
            folio = None

        if folio:
            chant.folio = folio

        # Concordances
        concordances = []
        for c in list(row["Concordances"]):
            matching_concordance = Concordance.objects.filter(letter_code=c)
            if matching_concordance:
                concordances.append(matching_concordance[0])

        # Along with the unsaved chant, store the concordances to add to it, and the
        # folio to add if it still needs to be created
        self.new_chant_info.append((chant, concordances, None if folio else folio_code))

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

    def determine_affected_entries(self):
        if self._affected_entries_determined:
            return

        # Get all the unique folios and manuscripts affected by adding the chants
        chants = [info[0] for info in self.new_chant_info]
        self.affected_folios = dict((chant.folio.pk, chant.folio)
                                    for chant in chants if chant.folio).values()

        self.affected_manuscripts = dict((folio.manuscript.pk, folio.manuscript)
                                         for folio in self.affected_folios).values()

        self._affected_entries_determined = True

    def delete_existing_chants(self):
        """Delete chants for all manuscripts we've encountered"""
        import solr
        from cantusdata import settings

        self.determine_affected_entries()

        # Disconnect the post_delete signals so that we don't update Solr yet
        # We'll do that in bulk afterward
        receivers = [
            'cantusdata_chant_solr_delete',
            'cantusdata_folio_decrement_chant_count',
            'cantusdata_manuscript_update_chant_count'
        ]

        manuscript_pks = [manuscript.pk for manuscript in self.affected_manuscripts]

        with signal_receivers_disconnected(*receivers):
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
                # sqlite has trouble with bulk deletion so we need to delete in increments
                increment = 100
                chants = [chant.pk for chant in Chant.objects.filter(manuscript__pk__in=manuscript_pks)]

                for i in xrange(0, len(chants), increment):
                    # Can't delete a slice so we need to query again
                    Chant.objects.filter(pk__in=chants[i:i + increment]).delete()

            else:
                Chant.objects.filter(manuscript__pk__in=manuscript_pks).delete()

        # All folios in the manuscripts will now be affected
        self.affected_folios = list(Folio.objects.filter(manuscript__pk__in=manuscript_pks))

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        manuscripts_query = ' OR '.join('manuscript_id:' + str(pk) for pk in manuscript_pks)
        solrconn.delete_query('type:cantusdata_chant AND ({})'.format(manuscripts_query))

        solrconn.commit()

    def save(self):
        self.determine_affected_entries()

        # Disconnect the post_save signals so that we don't update Solr yet
        # We'll do that in bulk afterward
        receivers = [
            'cantusdata_folio_solr_add',
            'cantusdata_folio_increment_chant_count',
            'cantusdata_manuscript_solr_add',
            'cantusdata_manuscript_update_chant_count'
        ]

        with signal_receivers_disconnected(*receivers):
            new_folio_map = {}

            for folio in self.new_folios:
                folio.save()

                # Keep track of the new folios so that we can add them to the chant field
                new_folio_map[folio.number] = folio

            for index, (chant, concordances, folio_code) in enumerate(self.new_chant_info):
                # We can now safely reference newly created folios
                if folio_code is not None:
                    chant.folio = new_folio_map[folio_code]

                chant.save()

                # Now that the chant is saved, add the concordances
                if concordances:
                    chant.concordances.add(*concordances)

                # Tracking
                if (index % 100) == 0:
                    self.stdout.write(u"{0} chants saved in the Django database.".format(index))

            # Update the chant counts
            for folio in self.affected_folios:
                folio.update_chant_count()

            for manuscript in self.affected_manuscripts:
                manuscript.update_chant_count()

    def update_solr(self):
        import solr
        from cantusdata import settings

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        # Build lists of all previously indexed values and all new values
        # to index

        new_records = []

        for (chant, _, _) in self.new_chant_info:
            new_records.append(chant.create_solr_record())

        for folio in self.affected_folios:
            new_records.append(folio.create_solr_record())

        for manuscript in self.affected_manuscripts:
            new_records.append(manuscript.create_solr_record())

        # Delete the old records
        existing_folio_query = ' OR '.join('item_id:' + str(folio.pk) for folio in self.affected_folios)
        existing_manuscript_query = ' OR '.join('item_id:' + str(man.pk) for man in self.affected_manuscripts)

        deletion_query = (
            '(type:cantusdata_folio AND ({0})) OR (type:cantusdata_manuscript AND ({1}))'
        ).format(existing_folio_query, existing_manuscript_query)

        solrconn.delete_query(deletion_query)

        # Add the new records
        solrconn.add_many(new_records)

        solrconn.commit()
