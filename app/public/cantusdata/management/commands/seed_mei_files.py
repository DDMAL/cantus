from os import listdir, makedirs, path, remove
from shutil import copy2
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from cantusdata.tasks import find_mei_file_for_folio

CURATED_MEI_DIR = path.join("/code", "production-mei-files")


class Command(BaseCommand):
    help = (
        "Copies a manuscript's curated MEI files into the live MEI tree "
        "(settings.MEI_FILES_DIR), which is where index_manuscript_mei reads from "
        "and where published deposits are written. Run this once per manuscript "
        "when setting up the MEI volume, and again whenever the curated archive is "
        "updated upstream.\n\n"
        "The point is that the live tree holds every folio of the manuscript. "
        "index_manuscript_mei takes a single --mei-dir, so a whole-manuscript "
        "reindex against a tree that only holds deposits would drop every folio "
        "that came from the curated archive."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "manuscript_id",
            type=int,
            help="The manuscript whose MEI files should be copied.",
        )
        parser.add_argument(
            "--from",
            dest="source_dir",
            type=str,
            default=CURATED_MEI_DIR,
            help=(
                "Directory holding per-manuscript MEI subdirectories. Defaults to "
                f"'{CURATED_MEI_DIR}'."
            ),
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help=(
                "Replace files that already exist in the live tree. Off by default, "
                "so a published deposit is not silently reverted to the curated "
                "version of the same folio."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        manuscript_id = options["manuscript_id"]
        source = path.join(options["source_dir"], str(manuscript_id))
        if not path.isdir(source):
            raise FileNotFoundError(f"No MEI directory for manuscript at {source}.")
        destination = path.join(settings.MEI_FILES_DIR, str(manuscript_id))
        makedirs(destination, exist_ok=True)

        mei_files = sorted(f for f in listdir(source) if f.endswith(".mei"))
        if not mei_files:
            raise FileNotFoundError(f"No MEI files found in {source}.")

        copied, skipped, replaced = 0, 0, 0
        for mei_file in mei_files:
            folio_number = mei_file.split("_")[-1].split(".")[0]
            # The folio's file may already be there under a different prefix --
            # a published deposit is named after the manuscript's siglum slug,
            # the curated archive after its own convention. Both name the same
            # folio to the indexer, so the tree must keep only one of them.
            existing_name = find_mei_file_for_folio(destination, folio_number)
            if existing_name is not None and not options["overwrite"]:
                skipped += 1
                continue
            if existing_name is not None and existing_name != mei_file:
                remove(path.join(destination, existing_name))
                replaced += 1
            copy2(path.join(source, mei_file), path.join(destination, mei_file))
            copied += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Copied {copied} MEI file(s) into {destination}"
                + (f", left {skipped} existing file(s) alone." if skipped else ".")
            )
        )
        if replaced:
            self.stdout.write(
                self.style.WARNING(
                    f"Replaced {replaced} file(s) that named the same folio under a "
                    "different filename -- any published deposit for those folios "
                    "is now the curated version on disk. Re-index the manuscript "
                    "so Solr matches."
                )
            )
        if skipped and not options["overwrite"]:
            self.stdout.write(
                "Pass --overwrite to replace the existing files with the curated "
                "versions."
            )
