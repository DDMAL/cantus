from django.core.management.base import BaseCommand
from django.db import transaction
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
from cantusdata.signals.solr_sync import solr_synchronizer
from cantusdata.helpers.chant_importer import ChantImporter
from cantusdata.helpers.source_importer import SourceImporter
import urllib.request
import urllib
from io import StringIO
from cantusdata.settings import BASE_DIR
from os import path
import csv


class Command(BaseCommand):
    """Imports Manuscripts and Chants from Cantus Database."""

    help = "Populates Manuscript and Chant django models"

    def add_arguments(self, parser):
        parser.add_argument("type", choices=["chants", "manuscripts", "iiif"])
        parser.add_argument(
            "--manuscript-id",
            type=int,
            dest="manuscript_id",
            help="Manuscript id (used only when importing chants)",
        )

        parser.add_argument(
            "--task",
            dest="task",
            help="Optional argument used when called from the django admin interface. Passes asynchronous task.",
        )

    def handle(self, *args, **options):
        with solr_synchronizer.get_session():
            self.stdout.write(f"Deleting old {options['type']} data...")
            task = options.get("task", None)
            if options["type"] == "chants":
                # manuscript-id is not optional for chants
                if options["manuscript_id"] is None:
                    self.stdout.write("Please provide a manuscript-id. Doing nothing.")
                else:
                    if task:
                        task.update_state(
                            state="STARTED",
                            meta={"chants_processed": 0, "chants_loaded": 0},
                        )
                    Chant.objects.filter(
                        manuscript__id=options["manuscript_id"]
                    ).delete()
                    self.stdout.write("Deleting old folio data...")
                    Folio.objects.filter(
                        manuscript__id=options["manuscript_id"]
                    ).delete()
                    self.import_chant_data(**options)
            elif options["type"] == "manuscripts":
                Manuscript.objects.all().delete()
                self.import_manuscript_data(**options)
            elif options["type"] == "iiif":
                Manuscript.objects.all().update(manifest_url="")
                self.import_iiif_data()
            self.stdout.write("Waiting for Solr to finish...")
        # Register that chants are loaded for this manuscript
        if options["type"] == "chants":
            mobj = Manuscript.objects.get(id=options["manuscript_id"])
            mobj.chants_loaded = True
            mobj.save()
        self.stdout.write("Done.")

    @transaction.atomic
    def import_manuscript_data(self, **options):
        self.stdout.write("Starting manuscript import process.")
        cdb_base_url = "https://cantusdatabase.org"
        source_importer = SourceImporter(cdb_base_url)
        source_ids = source_importer.request_source_ids()
        i = 0
        for source_id in source_ids:
            try:
                source = source_importer.get_source_data(source_id)
                # Getting the fields from the scraper
                id = source.get("id")
                name = source.get("name")
                cantusdb_url = f"{cdb_base_url}/source/{id}"
                csv_export_url = f"{cdb_base_url}/sites/default/files/csv/{id}.csv"
                siglum = source.get("siglum")
                date = source.get("date")
                provenance = source.get("provenance")
                description = source.get("description")
                # Populating the Manuscript model
                manuscript = Manuscript()
                manuscript.id = int(id)
                manuscript.name = name
                manuscript.cantus_url = cantusdb_url
                manuscript.csv_export_url = csv_export_url
                manuscript.siglum = siglum
                manuscript.date = date
                manuscript.provenance = provenance
                manuscript.description = description
                manuscript.is_mapped = "UNMAPPED"
                manuscript.save()
                self.stdout.write(f'{source["id"]} {source["name"]}')
                i += 1
            except urllib.error.HTTPError as http_error:
                if http_error.code == 403:
                    self.stdout.write(f"FORBIDDEN: {source_id}")
                else:
                    self.stdout.write(f"FAILED: {source_id}")
        self.stdout.write(f"Successfully imported {i} manuscripts into database.")

    def import_chant_data(self, **options):
        mobj = Manuscript.objects.get(id=options["manuscript_id"])
        scsv = urllib.request.urlopen(mobj.csv_export_url).read().decode("utf-8")
        task = options.get("task", None)
        # csv module can't handle csv as strings, so making it a file
        fcsv = StringIO(scsv)
        importer = ChantImporter(self.stdout, mobj=mobj)
        if task:
            chant_count = importer.import_csv(fcsv, task)
        else:
            chant_count = importer.import_csv(fcsv)
        # Save the new chants
        importer.save(task=task)
        self.stdout.write(f"Successfully imported {chant_count} chants into database.")

    @transaction.atomic
    def import_iiif_data(self):
        with open(
            f"{BASE_DIR}/data_dumps/manifests.csv", "r", encoding="utf-8"
        ) as file:
            iiif_reader = csv.DictReader(file)

            for row in iiif_reader:
                siglum = row["siglum"]
                manifest_url = row["manifest_url"]
                qs = Manuscript.objects.filter(siglum=siglum)
                if len(qs) > 0:
                    mobj = qs[0]
                    mobj.manifest_url = manifest_url
                    mobj.save()
