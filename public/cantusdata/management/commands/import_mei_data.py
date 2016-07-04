import os
import subprocess
import csv
import time

import progressbar

from django.core.management.base import BaseCommand
from django.conf import settings


UPLOAD_POLL_WAIT_SECS = 0.25
UPLOAD_PROGRESS_STEP = 5


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
            dump_to_csv(mei_location, siglum, csv_location)
            upload_to_solr(csv_location)

        elif mode == "csv_to_solr":
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

        files, pages = convert_mei(mei_location, siglum)

        prog_widgets = ['Parsing: ', progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()]
        prog_bar = progressbar.ProgressBar(widgets=prog_widgets, maxval=len(files))
        prog_bar.start()

        for page_idx, (file_name, page) in enumerate(pages):
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

            prog_bar.update(page_idx)

        prog_bar.finish()


def convert_mei(mei_location, siglum):
    return get_converter(siglum).convert(mei_location, siglum)


def get_converter(siglum):
    from cantusdata.helpers.mei_conversion import MEIConverter, StGallenMEIConverter

    if siglum == "ch-sgs-390" or siglum == "ch-sgs-391":
        return StGallenMEIConverter

    return MEIConverter


def upload_to_solr(filename):
    """Commit a CSV file to Solr using a stream"""

    prog_widgets = ['Uploading... ', progressbar.BouncingBar(), ' ', progressbar.Timer(format='Time: %s')]
    prog_bar = progressbar.ProgressBar(widgets=prog_widgets)
    prog_bar.start()

    # Build the Solr upload URL
    url = ('"{server}/update?stream.file={path}&stream.contentType=text/csv;charset=utf-8&commit=true"'
            .format(server=settings.SOLR_SERVER, path=os.path.abspath(filename)))

    command = 'curl -s -o /dev/null -w "%{http_code}" ' + url

    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

    polls = 0

    while proc.returncode is None:
        proc.poll()

        polls += 1

        prog_bar.update((polls * UPLOAD_PROGRESS_STEP) % prog_bar.maxval)
        time.sleep(UPLOAD_POLL_WAIT_SECS)

    prog_bar.finish()

    if proc.returncode != 0:
        failure_message = 'process returned {}'.format(proc.returncode)
    else:
        status = proc.communicate()[0]

        if status[0] != '2':
            failure_message = 'status {}'.format(status)

        else:
            failure_message = None

    if failure_message is not None:
        print 'Upload failed ({}). See the Solr logs for details.'.format(failure_message)
    else:
        print 'Upload successful.'

