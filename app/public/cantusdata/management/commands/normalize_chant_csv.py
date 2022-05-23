import csv
import re

from django.core.management.base import BaseCommand


W_REGEX = re.compile(r"^(\d+)w$")


class Command(BaseCommand):
    """Normalize chants exported from http://cantus.uwaterloo.ca for compatibility with the chant import script"""

    args = "filename.csv"

    def handle(self, *args, **options):
        target = args[0]

        self.stdout.write("Altering " + target)

        with open(target) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fields = reader.fieldnames

        # Rename fields
        rename_field(fields, rows, "", "Incipit")
        rename_field(fields, rows, "Full text (MS spelling)", "Fulltext")
        rename_field(fields, rows, "CAO Concordances", "Concordances")

        # Strip trailing underscore from the Cantus ID
        for row in rows:
            row["Cantus ID"] = row["Cantus ID"].strip(" _")

        # Rename folios [n]w to [n+1]r, for integer [n]
        # For context here see:
        #     https://github.com/DDMAL/cantus/issues/180
        #     https://github.com/DDMAL/cantus/issues/245
        for row in rows:
            old_folio = row["Folio"]
            match = W_REGEX.match(old_folio)

            if match:
                new_folio = str(int(match.group(1)) + 1) + "r"
                self.stdout.write(
                    "WARNING: Automatically renaming folio {} to {}!".format(
                        old_folio, new_folio
                    )
                )
                self.stdout.write(
                    "         You may want to manually verify or revert this change"
                )
                row["Folio"] = new_folio

        with open(target, "wb") as f:
            writer = csv.DictWriter(
                f, fields, lineterminator="\n", quoting=csv.QUOTE_ALL
            )
            writer.writeheader()

            for row in rows:
                writer.writerow(row)


def rename_field(fields, rows, old, new):
    try:
        old_index = fields.index(old)
    except ValueError:
        return

    fields[old_index] = new

    for row in rows:
        row[new] = row[old]
        del row[old]