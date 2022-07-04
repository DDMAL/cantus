from django.utils.text import slugify
from django.conf import settings
from django.db import transaction
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

    def import_csv(self, file_csv, task=None):
        index = 0
        try:
            csv_file = csv.DictReader(file_csv)
        except IOError:
            raise IOError("Could not read csv file")
        # Load in the csv file.  This is a massive list of dictionaries.
        self.stdout.write("Starting chant import process.")
        # Create chants and save them
        for index, row in enumerate(csv_file):
            self.add_chant(row)
            # Tracking
            if task:
                task.update_state(
                    state="PROGRESS",
                    meta={"chants_processed": index, "chants_loaded": 0},
                )
            if (index % 100) == 0:
                self.stdout.write("{0} chants processed for import.".format(index))
        return index

    def add_chant(self, row):
        """Get a chant object to save to the database.
        Prepare a folio object to add if necessary.
        """
        # Get the corresponding manuscript
        manuscript = self.get_manuscript(row["siglum"])
        # Throw exception if no corresponding manuscript
        if not manuscript:
            raise ValueError(
                "Manuscript with siglum={0} does not exist!".format(
                    slugify(str(row["siglum"]))
                )
            )
        chant = Chant()
        chant.marginalia = row["marginalia"].strip()
        chant.sequence = row["sequence"].strip()
        chant.cantus_id = row["cantus_id"].strip().rstrip(" _")
        chant.feast = row["feast"].strip()
        chant.office = expandr.expand_office(row["office"].strip())
        chant.genre = expandr.expand_genre(row["genre"].strip())
        chant.mode = expandr.expand_mode(row["mode"].strip())
        chant.differentia = expandr.expand_differentia(row["differentia"].strip())
        chant.finalis = row["finalis"].strip()
        chant.incipit = row["incipit"].strip()
        chant.full_text = row["fulltext_standardized"].strip()
        chant.volpiano = row["volpiano"].strip()
        chant.lit_position = self.position_expander.get_text(
            row["office"].strip(),
            row["genre"].strip(),
            row["position"].strip(),
        )
        chant.manuscript = manuscript
        folio_code = row["folio"]
        image_link = row["image_link"]
        # See if this folio already exists or is set to be created
        if (folio_code, manuscript.pk) not in self.folio_registry:
            try:
                folio = Folio.objects.get(number=folio_code, manuscript=manuscript)
            except Folio.DoesNotExist:
                # If the folio doesn't exist, prepare to create it
                self.add_folio(folio_code, manuscript, image_link)
                folio = None
        else:
            folio = None
        if folio:
            chant.folio = folio
        # Concordances
        concordances = []
        for c in list(row["cao_concordances"]):
            matching_concordance = Concordance.objects.filter(letter_code=c)
            if matching_concordance:
                concordances.append(matching_concordance[0])
        # Along with the unsaved chant, store the concordances to add to it, and the
        # folio to add if it still needs to be created
        self.new_chant_info.append((chant, concordances, None if folio else folio_code))

    def add_folio(self, folio_code, manuscript, image_link):
        folio = Folio()
        folio.number = folio_code
        folio.manuscript = manuscript
        folio.image_link = image_link
        self.new_folios.append(folio)
        self.folio_registry.add((folio_code, manuscript.pk))

    def get_manuscript(self, siglum):
        try:
            return self._manuscript_cache[siglum]
        except KeyError:
            manuscript = self._manuscript_cache[siglum] = Manuscript.objects.get(
                siglum=siglum
            )
            return manuscript

    @transaction.atomic
    def save(self, delete_existing=False, task=None):
        # Do all the updates within a single Solr session
        with solr_synchronizer.get_session():
            if delete_existing:
                self._delete_existing_chants()
            new_folio_map = {}
            for folio in self.new_folios:
                folio.save()
                # Keep track of the new folios so that we can add them to the chant field
                new_folio_map[folio.number] = folio
            total_chants = len(self.new_chant_info)
            for index, (chant, concordances, folio_code) in enumerate(
                self.new_chant_info
            ):
                # We can now safely reference newly created folios
                if folio_code is not None:
                    chant.folio = new_folio_map[folio_code]
                chant.save()
                # Now that the chant is saved, add the concordances
                if concordances:
                    chant.concordances.add(*concordances)
                # Tracking
                if task:
                    task.update_state(
                        state="PROGRESS",
                        meta={"chants_processed": total_chants, "chants_loaded": index},
                    )
                if (index % 100) == 0:
                    self.stdout.write(
                        "{0} chants saved in the Django database.".format(index)
                    )

    def _delete_existing_chants(self):
        manuscript_pks = set(
            chant.manuscript.pk for (chant, _, _) in self.new_chant_info
        )
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            # sqlite has trouble with bulk deletion so we need to delete in increments
            increment = 100
            chants = [
                chant.pk
                for chant in Chant.objects.filter(manuscript__pk__in=manuscript_pks)
            ]
            for i in range(0, len(chants), increment):
                # Can't delete a slice so we need to query again
                Chant.objects.filter(pk__in=chants[i : i + increment]).delete()
        else:
            Chant.objects.filter(manuscript__pk__in=manuscript_pks).delete()
