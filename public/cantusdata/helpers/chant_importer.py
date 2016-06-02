from django.utils.text import slugify
from django.conf import settings
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio
from cantusdata.models.concordance import Concordance
from cantusdata.models.manuscript import Manuscript
from cantusdata.helpers import expandr
from cantusdata.signals.solr_sync import solr_synchronizer
import csv


class ChantImporter:
    def __init__(self, stdout):
        self.stdout = stdout

        # Map siglum to manuscript model
        self._manuscript_cache = {}

        self.new_chant_info = []
        self.new_folios = []

        self.folio_registry = set()

        # Use position expander object to get correct positions
        self.position_expander = expandr.PositionExpander()

    def import_csv(self, file_name):
        index = 0

        # Load in the csv file.  This is a massive list of dictionaries.
        with open(file_name) as csv_file:
            csv_content = csv.DictReader(csv_file)
            self.stdout.write("Starting chant import process.")

            # Create chants and save them
            for index, row in enumerate(csv_content):
                self.add_chant(row)

                # Tracking
                if (index % 100) == 0:
                    self.stdout.write(u"{0} chants processed for import.".format(index))

        return index

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
        chant.cantus_id = row["Cantus ID"].strip().rstrip(' _').decode('utf-8')
        chant.feast = row["Feast"].strip().decode('utf-8')
        chant.office = expandr.expand_office(row["Office"].strip()).decode('utf-8')
        chant.genre = expandr.expand_genre(row["Genre"].strip()).decode('utf-8')
        chant.mode = expandr.expand_mode(row["Mode"].strip()).decode('utf-8')
        chant.differentia = expandr.expand_differentia(row["Differentia"].strip()).decode('utf-8')
        chant.finalis = row["Finalis"].strip().decode('utf-8')
        chant.incipit = row["Incipit"].strip().decode('utf-8')
        chant.full_text = row["Full text (standardized)"].strip().decode('utf-8')
        chant.volpiano = row["Volpiano"].strip().decode('utf-8')
        chant.lit_position = self.position_expander.get_text(
            row["Office"].strip(), row["Genre"].strip(),
            row["Position"].strip()).decode('utf-8')
        chant.manuscript = manuscript

        folio_code = row["Folio"].decode("utf-8")

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
        for c in list(row["CAO Concordances"]):
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

    def save(self, delete_existing=False):
        # Do all the updates within a single Solr session
        with solr_synchronizer.get_session():
            if delete_existing:
                self._delete_existing_chants()

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

    def _delete_existing_chants(self):
        manuscript_pks = set(chant.manuscript.pk for (chant, _, _) in self.new_chant_info)

        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            # sqlite has trouble with bulk deletion so we need to delete in increments
            increment = 100
            chants = [chant.pk for chant in Chant.objects.filter(manuscript__pk__in=manuscript_pks)]

            for i in xrange(0, len(chants), increment):
                # Can't delete a slice so we need to query again
                Chant.objects.filter(pk__in=chants[i:i + increment]).delete()

        else:
            Chant.objects.filter(manuscript__pk__in=manuscript_pks).delete()
