from os import makedirs, path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

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
            target = path.join(destination, submission.mei_filename)
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
