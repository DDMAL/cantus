from django.core.management.base import BaseCommand
from django.utils.text import slugify
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant
from cantusdata.models.concordance import Concordance
from cantusdata.models import Folio
from cantusdata.helpers import expandr
import sys
import csv


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        """
        Run "python manage.py import_chant_data filename.csv" to import a chant
        file into the db.  filename.csv must exist in /public/data_dumps/.
        """
        if args and args[0]:
            csv_file_name = args[0]
        else:
            raise ValueError("Please provide a file name!")

        # Load in the csv file.  This is a massive list of dictionaries.
        with open("data_dumps/" + str(csv_file_name)) as csv_file:
            csv_content = csv.DictReader(csv_file)
            self.stdout.write("Starting chant import process.")

            # Use position expander object to get correct positions
            self.position_expander = expandr.PositionExpander()

            # Create chants and save them
            for index, row in enumerate(csv_content):
                self.save_chant(row)

                # Tracking
                if (index % 100) == 0:
                    self.stdout.write(u"{0} chants imported.".format(index))

        self.stdout.write(
            u"Successfully imported {0} chants into database.".format(index))

    def save_chant(self, row):
        # Get the corresponding manuscript
        manuscript = Manuscript.objects.get(siglum=row["Siglum"])

        # Throw exception if no corresponding manuscript
        if not manuscript:
            raise ValueError(u"Manuscript with Siglum={0} does not exist!"
                             .format(slugify(unicode(row["Siglum"]))))

        chant = Chant()
        chant.marginalia = row["Marginalia"].strip().decode('utf-8')
        chant.sequence = row["Sequence"].strip().decode('utf-8')
        chant.cantus_id = row["Cantus ID"].strip().decode('utf-8')
        chant.feast = row["Feast"].strip().decode('utf-8')
        chant.office = expandr.expand_office(row["Office"].strip()).decode('utf-8')
        chant.genre = expandr.expand_genre(row["Genre"].strip()).decode('utf-8')
        chant.mode = expandr.expand_mode(row["Mode"].strip()).decode('utf-8')
        chant.differentia = expandr.expand_differentia(row["Differentia"].strip()).decode('utf-8')
        chant.finalis = row["Finalis"].strip().decode('utf-8')
        chant.incipit = row["Incipit"].strip().decode('utf-8')
        chant.full_text = row["Fulltext"].strip().decode('utf-8')
        chant.volpiano = row["Volpiano"].strip().decode('utf-8')
        chant.lit_position = self.position_expander.get_text(
            row["Office"].strip(), row["Genre"].strip(),
            row["Position"].strip()).decode('utf-8')
        chant.manuscript = manuscript

        folio_code = slugify(row["Folio"].decode("utf-8"))

        # See if this folio already exists
        try:
            folio = Folio.objects.get(number=folio_code,
                                      manuscript=manuscript)
        except Folio.DoesNotExist:
            # If the folio doesn't exist, create it
            folio = Folio()
            folio.number = folio_code
            folio.manuscript = manuscript
            folio.save()

        chant.folio = folio

        chant.save()

        # Concordances
        for c in list(row["Concordances"]):
            matching_concordance = Concordance.objects.filter(letter_code=c)
            if matching_concordance:
                chant.concordances.add(matching_concordance[0])