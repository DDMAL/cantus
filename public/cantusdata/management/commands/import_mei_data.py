import os
import subprocess
import csv

from django.core.management.base import BaseCommand
from django.conf import settings

from cantusdata.helpers.mei_conversion import MEIConverter, StGallenMEIConverter


class Command(BaseCommand):
    args = "mode manuscript"

    def handle(self, *args, **kwargs):
        if args and args[0] and args[1]:
            mode = args[0]
            manuscript = args[1]
        else:
            raise Exception("Please provide arguments for processing"
                            " mode and manuscript name.")

        # Make sure we're working with the right manuscript
        if manuscript == "salzinnes":
            self.stdout.write("Salzinnes manuscript selected.")
            siglum = "cdn-hsmu-m2149l4"
            mei_location = "data_dumps/mei/salz"
            csv_location = "data_dumps/mei_csv/salzinnes.csv"
        elif manuscript == "st_gallen_390":
            self.stdout.write("St. Gallen 390 manuscript selected.")
            siglum = "ch-sgs-390"
            mei_location = "data_dumps/mei/csg-390"
            csv_location = "data_dumps/mei_csv/csg-390.csv"
        elif manuscript == "st_gallen_391":
            self.stdout.write("St. Gallen 391 manuscript selected.")
            siglum = "ch-sgs-391"
            mei_location = "data_dumps/mei/csg-391"
            csv_location = "data_dumps/mei_csv/csg-391.csv"
        else:
            raise Exception("Please provide manuscript name!")

        if mode == "mei_to_csv":
            self.stdout.write("Dumping MEI to CSV.")
            dump_to_csv(mei_location, siglum, csv_location)
            self.stdout.write("MEI dumped to CSV.")

        elif mode == "mei_to_solr":
            self.stdout.write("Dumping MEI to CSV.")
            dump_to_csv(mei_location, siglum, csv_location)
            self.stdout.write("Committing CSV to Solr.")
            upload_to_solr(csv_location)
            self.stdout.write("MEI committed to Solr.")

        elif mode == "csv_to_solr":
            self.stdout.write('Committing CSV to Solr')
            upload_to_solr(csv_location)

        else:
            raise Exception("Please provide mode!")


def dump_to_csv(mei_location, siglum, path):
    """
    Dump the data to a CSV file.

    :param mei_location:
    :param siglum:
    :param path:
    :return:
    """
    # Maintain a stable heading order for Salzinnes-style CSV so that it's possible to run word-by-word
    # diffs on the output
    heading_order = {
        h: i for (i, h) in enumerate((
            'folio', 'pnames', 'neumes', 'siglum_slug', 'intervals', 'id',
            'semitones', 'contour', 'project', 'location', 'type'
        ))
    }

    with open(path, 'wb') as csv_file:
        writer = None

        for page in convert_mei(mei_location, siglum):
            for row in page:
                if writer is None:
                    # We can only initialize the header once we have the first row

                    # FIXME(wabain): This assumes that the first row will contain all the
                    #   fields we're interested in, but that's not necessarily the case.
                    #
                    #   If the assumption breaks we'll get a ValueError: dict contains fields
                    #   not in fieldname.
                    headings = list(sorted(row.keys(), key=lambda h: heading_order.get(h, -1)))

                    writer = csv.DictWriter(csv_file, headings)
                    writer.writeheader()

                writer.writerow(row)


def convert_mei(mei_location, siglum):
    return get_converter(siglum).convert(mei_location, siglum)


def get_converter(siglum):
    if siglum == "ch-sgs-390" or siglum == "ch-sgs-391":
        return StGallenMEIConverter

    return MEIConverter


def upload_to_solr(filename):
    """Commit a CSV file to Solr using a stream"""

    # Build the Solr upload URL
    url = ('"{server}/update?stream.file={path}&stream.contentType=text/csv;charset=utf-8&commit=true"'
            .format(server=settings.SOLR_SERVER, path=os.path.abspath(filename)))

    command = 'curl -s -o /dev/null -w "%{http_code}" ' + url

    status = subprocess.check_output(command, shell=True)

    if not status or status[0] != '2':
        print 'Upload failed (status {}). See the Solr logs for details.'.format(status)
    else:
        print 'CSV upload successful.'

