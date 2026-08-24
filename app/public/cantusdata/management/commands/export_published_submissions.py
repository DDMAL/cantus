from os import makedirs, path, sep
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from cantusdata.models.mei_submission import MEISubmission, SubmissionStatus


class Command(BaseCommand):
    help = (
        "Writes a manuscript's published MEI submissions out to a directory, for a "
        "maintainer to commit into the curated production_mei_files archive.\n\n"
        "Promotion into the curated archive stays a deliberate human act: this "
        "command hands over the files, it does not push anything anywhere."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "manuscript_id",
            type=int,
            help="The manuscript whose published submissions should be exported.",
        )
        parser.add_argument(
            "--out",
            dest="out_dir",
            type=str,
            required=True,
            help=(
                "Directory to write into. Files land in <out>/<manuscript_id>/, "
                "matching the layout the curated archive uses."
            ),
        )

    def resolve_target(self, destination: str, submission: MEISubmission) -> str:
        """
        Where one submission's MEI is written, once confirmed to be inside
        `destination`.

        mei_filename is built from the manuscript's siglum, which slugify
        flattens, and the folio number, which is not transformed at all. Folio
        numbers reaching here are canonical Folio.number values, so none of them
        currently contain a separator -- but this opens a file for writing from
        a database-derived name, and a name that escaped the directory would
        overwrite whatever it landed on. Checked rather than assumed.
        """
        filename = submission.mei_filename
        target = path.normpath(path.join(destination, filename))
        contained = path.abspath(target).startswith(path.abspath(destination) + sep)
        if path.dirname(filename) or not contained:
            raise CommandError(
                f"Submission {submission.pk} (f. {submission.folio_number}) would be "
                f"written to {target!r}, outside the export directory. Its folio "
                "number contains a path separator; fix the folio record before "
                "exporting."
            )
        return target

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

        destination = path.join(options["out_dir"], str(manuscript_id))
        makedirs(destination, exist_ok=True)
        for submission in submissions:
            target = self.resolve_target(destination, submission)
            with open(target, "w", encoding="utf-8") as out_file:
                out_file.write(submission.mei)
            self.stdout.write(
                f"{target}  (f. {submission.folio_number}, from "
                f"{submission.submitter})"
            )
        self.stdout.write(
            self.style.SUCCESS(f"Exported {len(submissions)} file(s) to {destination}.")
        )
        return None
