import os
import subprocess
import csv

import solr

from django.core.management.base import BaseCommand
from django.conf import settings

from cantusdata.helpers.mei_conversion import MEIConverter, StGallenMEIConverter
from cantusdata.helpers.parsers.csv_parser import CSVParser


def convert_mei(mei_location, siglum):
    return get_converter(siglum).convert(mei_location, siglum)


def get_converter(siglum):
    if siglum == "ch-sgs-390" or siglum == "ch-sgs-391":
        return StGallenMEIConverter

    return MEIConverter


class Command(BaseCommand):
    args = "mode manuscript"

    def handle(self, *args, **kwargs):
        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        mode = None
        manuscript = None
        # Grab the terminal params
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

            data = convert_mei(mei_location, siglum)

            self.data_to_csv(data, csv_location)
            self.stdout.write("MEI dumped to CSV.")

        elif mode == "mei_to_solr":
            self.stdout.write("Committing MEI to Solr.")

            data = convert_mei(mei_location, siglum)

            self.data_to_solr(data, solrconn)
            self.stdout.write("MEI committed to Solr.")

        elif mode == "csv_to_solr":
            self.csv_to_solr(csv_location)

        elif mode == "gall_hack":
            data = CSVParser("data_dumps/hacky_csv_mei/csg_390_ordered_2.csv",
                             "ch-sgs-390").parse()
            self.data_to_solr(data, solrconn)

        else:
            raise Exception("Please provide mode!")

    def data_to_csv(self, data, path):
        """
        Dump the data to a CSV file.

        :param data:
        :param path:
        :return:
        """
        heading_order = {
            h: i for (i, h) in enumerate((
                'folio', 'pnames', 'neumes', 'siglum_slug', 'intervals', 'id',
                'semitones', 'contour', 'project', 'location', 'type'
            ))
        }

        # Maintain a stable heading order for Salzinnes-style CSV so that it's possible to run word-by-word
        # diffs on the output
        headings = list(sorted(data[0][0].keys(), key=lambda h: heading_order.get(h, -1)))

        csv_file = open(path, 'wb')
        w = csv.DictWriter(csv_file, headings)
        w.writeheader()
        for page in data:
            for row in page:
                w.writerow(row)
        csv_file.close()

    def data_to_solr(self, data, solrconn):
        """
        Commit the data to Solr.

        :param data:
        :param solrconn:
        :return:
        """
        rows = []

        for page in data:
            rows.extend(page)

        solrconn.add_many(rows)
        solrconn.commit()

    def csv_to_solr(self, filename):
        """Commit a CSV file to Solr using a stream"""

        # Build the Solr upload URL
        url = ('"{server}/update?stream.file={path}&stream.contentType=text/csv;charset=utf-8&commit=true"'
                .format(server=settings.SOLR_SERVER, path=os.path.abspath(filename)))

        command = 'curl -s -o /dev/null -w "%{http_code}" ' + url

        print 'Sending CSV to Solr.'

        status = subprocess.check_output(command, shell=True)

        if not status or status[0] != '2':
            print 'Upload failed (status {}). See the Solr logs for details.'.format(status)
        else:
            print 'CSV upload successful.'

