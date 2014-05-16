from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant
from cantusdata.helpers.csv_tools import CSVParser


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        """
        Run "python manage.py import_all_data filename.csv" to import a chant
        file into the db.  filename.csv must exist in /public/data_dumps/.
        """
        csv_file_name = args[0]
        # Nuke the db chants
        Chant.objects.all().delete()
        # Load in the csv file.  This is a massive list of dictionaries.
        csv_file = CSVParser("data_dumps/" + str(csv_file_name))
        # Create a chant and save it
        for row in csv_file.parsed_data:
            # Get the corresponding manuscript
            manuscript_list = Manuscript.objects.filter(siglum=row["Siglum"])
            # Throw exception if no corresponding manuscript
            if not manuscript_list:
                raise NameError(u"Manuscript with Siglum={0} does not exist!".format(row["Siglum"]))

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
            chant.manuscript = manuscript_list[0]
            chant.save()
        self.stdout.write("Successfully imported chants into database.")
