from django.core.management.base import BaseCommand
from django.db import transaction
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio
from cantusdata.models.concordance import Concordance
from cantusdata.models.manuscript import Manuscript
from cantusdata.signals.solr_sync import solr_synchronizer
from cantusdata.helpers.chant_importer import ChantImporter
from cantusdata.helpers.scrapers.sources import sources
from cantusdata.helpers.scrapers.manuscript import parse as parse_manuscript
from cantusdata.helpers.scrapers.concordances import concordances
import urllib.request
from io import StringIO
from cantusdata.settings import BASE_DIR
from os import path


class Command(BaseCommand):
    """Imports Manuscripts, Concordances, and Chants from Cantus Database."""

    help = "Populates Manuscript, Concordance, and Chant django models"

    def add_arguments(self, parser):
        parser.add_argument(
            "type", choices=["chants", "concordances", "manuscripts", "iiif"]
        )
        parser.add_argument(
            "--manuscript-id",
            type=int,
            dest="manuscript_id",
            help="Manuscript id (used only when importing chants)",
        )

    def handle(self, *args, **options):
        with solr_synchronizer.get_session():
            self.stdout.write(
                "Deleting old {0} data...".format(options["type"])
            )
            if options["type"] == "chants":
                # manuscript-id is not optional for chants
                if options["manuscript_id"] is None:
                    self.stdout.write(
                        "Please provide a manuscript-id. Doing nothing."
                    )
                else:
                    Chant.objects.filter(
                        manuscript__id=options["manuscript_id"]
                    ).delete()
                    self.stdout.write("Deleting old folio data...")
                    Folio.objects.filter(
                        manuscript__id=options["manuscript_id"]
                    ).delete()
                    self.import_chant_data(**options)
            elif options["type"] == "concordances":
                Concordance.objects.all().delete()
                self.import_concordance_data(**options)
            elif options["type"] == "manuscripts":
                Manuscript.objects.all().delete()
                self.import_manuscript_data(**options)
            elif options["type"] == "iiif":
                Manuscript.objects.all().update(manifest_url="")
                self.import_iiif_data()
            self.stdout.write("Waiting for Solr to finish...")
        self.stdout.write("Done.")

    @transaction.atomic
    def import_manuscript_data(self, **options):
        self.stdout.write("Starting manuscript import process.")
        i = 0
        for source, name in sources.items():
            self.stdout.write(source + " " + name)
            # Getting the fields from the scraper
            metadata = parse_manuscript(source)
            name = metadata.get("Title", "")
            cantus_url = metadata.get("CantusURL", "")
            csv_export_url = metadata.get("CSVExport", "")
            siglum = metadata.get("Siglum", "")
            date = metadata.get("Date", "")
            provenance = metadata.get("Provenance", "")
            description = metadata.get("Summary", "")
            # Populating the Manuscript model
            manuscript = Manuscript()
            manuscript.name = name
            manuscript.cantus_url = cantus_url
            manuscript.csv_export_url = csv_export_url
            manuscript.siglum = siglum
            manuscript.date = date
            manuscript.provenance = provenance
            manuscript.description = description
            manuscript.save()
            i += 1
        self.stdout.write(
            "Successfully imported {} manuscripts into database.".format(i)
        )

    @transaction.atomic
    def import_concordance_data(self, **options):
        for idx, c in enumerate(concordances):
            concordance = Concordance()
            concordance.letter_code = c["letter_code"]
            concordance.institution_city = c["institution_city"]
            concordance.institution_name = c["institution_name"]
            concordance.library_manuscript_name = c["library_manuscript_name"]
            concordance.date = c["date"]
            concordance.location = c["location"]
            concordance.rism_code = c["rism_code"]
            concordance.save()
        self.stdout.write(
            "Successfully imported {} concordances into database.".format(
                idx + 1
            )
        )

    def import_chant_data(self, **options):
        mobj = Manuscript.objects.get(id=options["manuscript_id"])
        scsv = (
            urllib.request.urlopen(mobj.csv_export_url).read().decode("utf-8")
        )
        # csv module can't handle csv as strings, so making it a file
        fcsv = StringIO(scsv)
        importer = ChantImporter(self.stdout)
        chant_count = importer.import_csv(fcsv)
        # Save the new chants
        importer.save()
        # Register that chants are loaded for this manuscript
        mobj.chants_loaded = True
        mobj.save()
        self.stdout.write(
            "Successfully imported {} chants into database.".format(
                chant_count
            )
        )

    @transaction.atomic
    def import_iiif_data(self):
        with open(path.join(BASE_DIR, "data_dumps", "manifests.csv"), "r") as file:
            csv = file.readlines()

        for row in csv:
            siglum, manifest_url = row.strip().split(",")
            qs = Manuscript.objects.filter(siglum=siglum)
            if len(qs) > 0:
                mobj = qs[0]
                mobj.manifest_url = manifest_url
                mobj.save()
