from django.core.management.base import BaseCommand
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.plugin import Plugin
import csv


class Command(BaseCommand):

    CSV_PATH = "data_dumps/public-manuscripts.csv"

    help = (
        "Reads the file '{0}' and updates manuscripts accordingly."
        "\nSets all manuscripts found in this file to public=True.".format(CSV_PATH)
    )

    def handle(self, *args, **options):
        try:
            csv_file = csv.DictReader(open(self.CSV_PATH, "rU"))
        except IOError:
            raise IOError("File '{0}' does not exist!".format(self.CSV_PATH))

        self.stdout.write("Starting update process.")

        for index, row in enumerate(csv_file):
            try:
                manuscript = Manuscript.objects.get(id=row["id"])
            except Manuscript.DoesNotExist:
                self.stdout.write("Manuscript {0} does not exist".format(row["id"]))
                continue

            self.stdout.write("Updating manuscript {0}".format(row["id"]))

            manuscript.public = True
            manuscript.cantus_url = row["cantus_url"].decode("utf-8").strip()
            manuscript.manifest_url = row["manifest_url"].decode("utf-8").strip()

            # Parse plugins
            plugin_column = row["plugins"].decode("utf-8").strip()
            if len(plugin_column) > 0:
                plugin_strings = plugin_column.split(",")
                manuscript.plugins.clear()

                for plugin_string in plugin_strings:
                    try:
                        plugin = Plugin.objects.get(name=plugin_string)
                        manuscript.plugins.add(plugin)
                    except Plugin.DoesNotExist:
                        self.stdout.write(
                            "Plugin {0} does not exist".format(plugin_string)
                        )
                        continue

            # Note that this will also refresh Solr chants if the 'public' field has changed
            # See the Manuscript model for more info
            manuscript.save()

        self.stdout.write(
            "Successfully updated {0} public manuscripts.".format(index + 1)
        )
