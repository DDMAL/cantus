import solr
import csv
from django.core.management.base import BaseCommand
from cantusdata import settings
from cantusdata.helpers.parsers.csv_parser import CSVParser


class Command(BaseCommand):
    args = ""

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
            if manuscript == "st_gallen_390" or manuscript == "st_gallen_391":
                from cantusdata.helpers.parsers.gallen_mei2_parser import GallenMEI2Parser
                parser = GallenMEI2Parser(mei_location, siglum)
            else:
                from cantusdata.helpers.parsers.mei2_parser import MEI2Parser
                parser = MEI2Parser(mei_location, siglum)
            data = parser.parse()
            self.data_to_csv(data, csv_location)
            self.stdout.write("MEI dumped to CSV.")
        elif mode == "mei_to_solr":
            self.stdout.write("Committing MEI to Solr.")
            if manuscript == "st_gallen_390" or manuscript == "st_gallen_391":
                from cantusdata.helpers.parsers.gallen_mei2_parser import GallenMEI2Parser
                parser = GallenMEI2Parser(mei_location, siglum)
            else:
                from cantusdata.helpers.parsers.mei2_parser import MEI2Parser
                parser = MEI2Parser(mei_location, siglum)
            data = parser.parse()
            self.data_to_solr(data, solrconn)
            self.stdout.write("MEI committed to Solr.")
        elif mode == "csv_to_solr":
            self.stdout.write("Loading CSV file...")
            data = csv.DictReader(open(csv_location))
            self.stdout.write("Adding CSV to Solr...")
            solrconn.add_many(list(data))
            self.stdout.write("Committing Solr additions.")
            solrconn.commit()
            self.stdout.write("CSV committed to Solr.")
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
        csv_file = open(path, 'wb')
        w = csv.DictWriter(csv_file, data[0][0].keys())
        w.writeheader()
        for page in data:
            for row in page:
                w = csv.DictWriter(csv_file, row.keys())
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
