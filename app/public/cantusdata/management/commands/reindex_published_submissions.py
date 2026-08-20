from os import path
from typing import Any

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandParser

from cantusdata.models.mei_submission import MEISubmission, SubmissionStatus
from cantusdata.tasks import write_submission_to_mei_dir


class Command(BaseCommand):
    help = (
        "Rebuilds the notation index for every published MEI submission of a "
        "manuscript, restoring any missing file from the database first.\n\n"
        "This is the recovery path after a Solr rebuild, and the repair path if "
        "the MEI volume is ever restored from a backup older than the database: "
        "the submitted MEI is stored in Postgres, so the volume can always be "
        "reconstructed from it."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "manuscript_id",
            type=int,
            help="The manuscript whose published submissions should be reindexed.",
        )
        parser.add_argument(
            "--files-only",
            action="store_true",
            help="Restore missing MEI files but do not touch the Solr index.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        manuscript_id = options["manuscript_id"]
        submissions = MEISubmission.objects.filter(
            manuscript_id=manuscript_id, status=SubmissionStatus.PUBLISHED
        ).select_related("manuscript")
        if not submissions:
            self.stdout.write(
                f"No published submissions for manuscript {manuscript_id}."
            )
            return None

        restored, reindexed = 0, 0
        for submission in submissions:
            expected = submission.published_path or path.join(
                settings.MEI_FILES_DIR,
                str(manuscript_id),
                submission.mei_filename,
            )
            if not path.exists(expected):
                written = write_submission_to_mei_dir(submission)
                if written != submission.published_path:
                    submission.published_path = written
                    submission.save(update_fields=["published_path"])
                restored += 1
                self.stdout.write(f"Restored {written} from the database.")
            if options["files_only"]:
                continue
            call_command(
                "index_manuscript_mei",
                str(manuscript_id),
                "--folio",
                submission.folio_number,
                "--replace",
                "--mei-dir",
                settings.MEI_FILES_DIR,
            )
            reindexed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Restored {restored} file(s); reindexed {reindexed} folio(s) for "
                f"manuscript {manuscript_id}."
            )
        )
        return None
