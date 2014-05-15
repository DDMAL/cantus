from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant
from cantusdata.helpers.csv_tools import CSVParser


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        csv_file_name = args[0]
        # Nuke the db chants
        # TODO: Figure out what the problem with this deleting is!
        Chant.objects.all().delete()
        # Load in the csv file.  This is a massive list of dictionaries.
        csv_file = CSVParser("data_dumps/" + str(csv_file_name))
        # Temporary manuscript for testing
        # TODO: Implement proper chant -> manuscript mapping
        manuscript = Manuscript.objects.filter(id=2)[0]
        # Create a chant and save it
        for row in csv_file.parsed_data:
            chant = Chant()
            chant.marginalia = row["Marginalia"]
            chant.folio = row["Folio"]
            chant.sequence = row["Sequence"]
            chant.cantus_id = row["Cantus ID"]
            chant.feast = row["Feast"]
            chant.office = row["Office"]
            chant.genre = row["Genre"]
            chant.lit_position = row["Position"]
            chant.mode = row["Mode"]
            chant.differentia = row["Differentia"]
            chant.finalis = row["Finalis"]
            chant.incipit = row["Incipit"]
            chant.full_text = row["Fulltext"]
            chant.concordances = row["Concordances"]
            chant.volpiano = row["Volpiano"]
            chant.manuscript = manuscript
            chant.save()
        self.stdout.write("Successfully imported chants into database.")
