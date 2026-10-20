from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.mei_submission import MEISubmission
from cantusdata.signals.solr_sync import solr_synchronizer
from cantusdata.helpers.chant_importer import ChantImporter
from cantusdata.helpers.source_importer import CANTUSDB_TIMEOUT, SourceImporter
from cantusdata.metrics.definitions import CHANTS_IMPORTED
from cantusdata.metrics.tracking import track_external
import urllib.request
import urllib
from io import StringIO
from cantusdata.settings import BASE_DIR
from os import path
import csv

CANTUSDB_URL = "https://cantusdatabase.org"
# The CANTUS Database fields a manuscripts import refreshes. Everything else on
# a manuscript (public, chants_loaded, is_mapped, manifest_url, plugins, ...) is
# local work, which an import never touches.
SOURCE_FIELDS = (
    "name",
    "cantus_url",
    "csv_export_url",
    "siglum",
    "date",
    "provenance",
    "description",
)
# More failed sources than this means CANTUS Database is struggling, not that
# those sources are broken: write nothing rather than half an import.
MAX_FAILED_FRACTION = 0.2
# --prune trusts the source list only if it is at least this much of what we
# already have; a truncated list must not read as mass deletion.
MIN_LISTED_FRACTION_FOR_PRUNE = 0.5


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
        parser.add_argument(
            "--prune",
            action="store_true",
            help=(
                "With `manuscripts`: delete manuscripts that are no longer in "
                "CANTUS Database, if nothing has been done with them locally."
            ),
        )

    def handle(self, *args, **options):
        if options["type"] == "manuscripts":
            self.import_manuscript_data(prune=options["prune"])
            self.stdout.write("Done.")
            return
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

    def import_manuscript_data(self, prune=False):
        """
        Refresh manuscripts from CANTUS Database, updating them in place.

        Everything is fetched before anything is written, so the write is one
        short transaction rather than one held open across a thousand HTTP
        requests (and the row locks with it).
        """
        self.stdout.write("Fetching sources from CANTUS Database...")
        source_importer = SourceImporter(CANTUSDB_URL)
        listed_ids = {
            int(source_id) for source_id in source_importer.request_source_ids()
        }
        fetched, failed = {}, []
        for source_id in sorted(listed_ids):
            try:
                source = source_importer.get_source_data(source_id)
            except (OSError, KeyError, TypeError, ValueError) as error:
                # OSError covers HTTP, connection and timeout errors; the rest
                # are malformed responses.
                self.stdout.write(f"FAILED: {source_id} ({error})")
                failed.append(source_id)
                continue
            fetched[source_id] = self._source_values(source_id, source)
        if listed_ids and len(failed) > MAX_FAILED_FRACTION * len(listed_ids):
            raise CommandError(
                f"{len(failed)} of {len(listed_ids)} sources could not be fetched. "
                "Nothing was changed."
            )

        with solr_synchronizer.get_session(), transaction.atomic():
            created, updated, unchanged = self._upsert_manuscripts(fetched)
            pruned = self._report_vanished(listed_ids, prune)
        self.stdout.write(
            f"Created {created}, updated {updated}, unchanged {unchanged}, "
            f"failed {len(failed)}, pruned {pruned}."
        )

    def _source_values(self, source_id, source):
        values = {
            "name": source.get("name"),
            "cantus_url": f"{CANTUSDB_URL}/source/{source_id}",
            "csv_export_url": f"{CANTUSDB_URL}/sites/default/files/csv/{source_id}.csv",
            "siglum": source.get("siglum"),
            "date": source.get("date"),
            "provenance": source.get("provenance"),
            "description": source.get("description"),
        }
        # One over-long value must not roll back the whole import.
        for field, value in values.items():
            max_length = Manuscript._meta.get_field(field).max_length
            if max_length and isinstance(value, str) and len(value) > max_length:
                self.stdout.write(f"TRUNCATED: {source_id} {field}")
                values[field] = value[:max_length]
        return values

    def _upsert_manuscripts(self, fetched):
        created = updated = unchanged = 0
        existing = Manuscript.objects.in_bulk(list(fetched))
        for source_id, values in fetched.items():
            manuscript = existing.get(source_id)
            if manuscript is None:
                Manuscript.objects.create(id=source_id, **values)
                created += 1
                continue
            changed = [f for f in SOURCE_FIELDS if getattr(manuscript, f) != values[f]]
            if not changed:
                # Saving would still reindex it in Solr.
                unchanged += 1
                continue
            for field in changed:
                setattr(manuscript, field, values[field])
            manuscript.save(update_fields=changed)
            updated += 1
        return created, updated, unchanged

    def _report_vanished(self, listed_ids, prune):
        """
        List manuscripts CANTUS Database no longer lists; delete them with --prune.

        Only the source list decides what has vanished: a source that merely
        failed to fetch this time is still listed.
        """
        vanished = list(Manuscript.objects.exclude(pk__in=listed_ids).order_by("pk"))
        if not vanished:
            return 0
        self.stdout.write(
            f"{len(vanished)} manuscript(s) are no longer in CANTUS Database:"
        )
        existing = Manuscript.objects.count()
        if prune and len(listed_ids) < MIN_LISTED_FRACTION_FOR_PRUNE * existing:
            self.stdout.write(
                f"Not pruning: CANTUS Database listed {len(listed_ids)} sources "
                f"for {existing} manuscripts here, which looks like a partial list."
            )
            prune = False
        pruned = 0
        for manuscript in vanished:
            blockers = self._prune_blockers(manuscript)
            if prune and not blockers:
                self.stdout.write(f"  {manuscript.pk} {manuscript}: deleted")
                manuscript.delete()
                pruned += 1
            elif blockers:
                self.stdout.write(
                    f"  {manuscript.pk} {manuscript}: kept ({', '.join(blockers)})"
                )
            else:
                self.stdout.write(
                    f"  {manuscript.pk} {manuscript}: --prune would delete"
                )
        return pruned

    @staticmethod
    def _prune_blockers(manuscript):
        """What has been done with a manuscript locally, which a prune must not lose."""
        blockers = []
        if manuscript.public:
            blockers.append("public")
        if manuscript.chants_loaded:
            blockers.append("chants loaded")
        if manuscript.is_mapped != "UNMAPPED":
            blockers.append(f"folios {manuscript.is_mapped.lower()}")
        if manuscript.manifest_url:
            blockers.append("has a manifest")
        if manuscript.viewer_warning:
            blockers.append("has a viewer warning")
        if manuscript.plugins.exists():
            blockers.append("has plugins")
        if Chant.objects.filter(manuscript=manuscript).exists():
            blockers.append("has chants")
        if Folio.objects.filter(manuscript=manuscript).exists():
            blockers.append("has folios")
        if MEISubmission.objects.filter(manuscript=manuscript).exists():
            blockers.append("has MEI submissions")
        return blockers

    def import_chant_data(self, **options):
        mobj = Manuscript.objects.get(id=options["manuscript_id"])
        with track_external("cantusdb", mobj.csv_export_url):
            scsv = (
                urllib.request.urlopen(mobj.csv_export_url, timeout=CANTUSDB_TIMEOUT)
                .read()
                .decode("utf-8")
            )
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
        CHANTS_IMPORTED.labels(str(mobj.pk)).inc(chant_count)
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
