import csv

from django.core.management.base import BaseCommand


class Command (BaseCommand):
    """Normalize chants exported from http://cantus.uwaterloo.ca for compatibility with the chant import script"""

    args = 'filename.csv'

    def handle(self, *args, **options):
        target = args[0]

        self.stdout.write('Altering ' + target)

        with open(target) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fields = reader.fieldnames

        # Rename fields
        rename_field(fields, rows, '', 'Incipit')
        rename_field(fields, rows, 'Full text (MS spelling)', 'Fulltext')
        rename_field(fields, rows, 'CAO Concordances', 'Concordances')

        # Strip trailing underscore from the Cantus ID
        for row in rows:
            row['Cantus ID'] = row['Cantus ID'].strip(' _')

        with open(target, 'wb') as f:
            writer = csv.DictWriter(f, fields, quoting=csv.QUOTE_ALL)
            writer.writeheader()

            for row in rows: writer.writerow(row)


def rename_field(fields, rows, old, new):
    fields[fields.index(old)] = new

    for row in rows:
        row[new] = row[old]
        del row[old]