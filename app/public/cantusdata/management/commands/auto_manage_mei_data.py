from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils.text import slugify
import subprocess
import datetime
import logging


class Command(BaseCommand):
    args = ""

    mei_data_locations = {
        # 'st_gallen_390': "data_dumps/mei/csg-390",
        # 'st_gallen_391': None,
        "salzinnes": "data_dumps/mei/salz"
    }

    def handle(self, *args, **kwargs):
        logging.basicConfig(
            filename="logs/mei_changes/changelog.log",
            level=logging.INFO,
            format="%(asctime)s %(message)s",
        )
        # We use this log file to keep track of what happens
        # log = open("logs/mei_changes/changelog.txt", 'wa')
        logging.info("########### Begin session ################")
        for manuscript in list(self.mei_data_locations.keys()):
            # Open the log file
            try:
                manuscript_log_file = open(
                    "logs/mei_changes/{0}.txt".format(manuscript), "r+"
                )
            except IOError:
                # If the file didn't already exist...
                open("logs/mei_changes/{0}.txt".format(manuscript), "w").close()
                manuscript_log_file = open(
                    "logs/mei_changes/{0}.txt".format(manuscript), "w+"
                )
            # Grab the console output
            console_output = slugify(
                "{0}".format(
                    subprocess.check_output(
                        ["ls", "-l", self.mei_data_locations[manuscript]]
                    )
                )
            )
            if console_output != manuscript_log_file.read():
                manuscript_log_file.write(console_output)
                logging.info("{0} has changed!".format(manuscript))
                # Flush the old version of that manuscript from Solr
                call_command("remove_mei_data", manuscript)
                logging.info("{0} removed from Solr.".format(manuscript))
                # Reimport the manuscript
                call_command("import_mei_data", "mei_to_solr", manuscript)
                logging.info("New {0} imported into Solr.".format(manuscript))

            else:
                logging.info("{0} has not changed.".format(manuscript))
            # We're done with this file
            manuscript_log_file.close()
        logging.info("########### End session ##################")
        # print console_output
        # # Call a command
        # call_command("auto_manage_mei_data")
