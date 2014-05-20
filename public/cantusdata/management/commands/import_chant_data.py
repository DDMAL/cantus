from django.core.management.base import BaseCommand
from django.utils.text import slugify
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant
from cantusdata.models.concordance import Concordance
from cantusdata.helpers import expandr
import sys
import csv


class Command(BaseCommand):
    args = ""
    debug = True

    def handle(self, *args, **kwargs):
        """
        Run "python manage.py import_chant_data filename.csv" to import a chant
        file into the db.  filename.csv must exist in /public/data_dumps/.
        """
        if args:
            csv_file_name = args[0]
        else:
            self.stdout.write("Please provide a file name!")
            sys.exit(-1)
        try:
            csv_file = csv.DictReader(open("data_dumps/" + str(csv_file_name)))
        except IOError:
            self.stdout.write(u"File {0} does not exist!".format(csv_file_name))
            sys.exit(-1)
        if self.debug:
            self.stdout.write("Deleting all old chant data...")
            # Nuke the db chants
            Chant.objects.all().delete()
            self.stdout.write("Old chant data deleted.")
        # Load in the csv file.  This is a massive list of dictionaries.

        self.stdout.write("Starting chant import process.")
        # Use position expander object to get correct positions
        position_expander = expandr.PositionExpander()
        # Create a chant and save it
        for index, row in enumerate(csv_file):
            # Get the corresponding manuscript
            manuscript_list = Manuscript.objects.filter(
                siglum_slug=slugify(unicode(row["Siglum"])))
            # Throw exception if no corresponding manuscript
            if not manuscript_list:
                raise NameError(u"Manuscript with Siglum={0} does not exist!".format(slugify(unicode(row["Siglum"]))))

            chant = Chant()
            chant.marginalia = row["Marginalia"]
            chant.folio = row["Folio"]
            chant.sequence = row["Sequence"]
            chant.cantus_id = row["Cantus ID"]
            chant.feast = row["Feast"]
            chant.office = expandr.expand_office(row["Office"])
            chant.genre = expandr.expand_genre(row["Genre"])
            chant.mode = expandr.expand_mode(row["Mode"])
            chant.differentia = row["Differentia"]
            chant.finalis = row["Finalis"]
            chant.incipit = row["Incipit"]
            chant.full_text = row["Fulltext"]
            chant.volpiano = row["Volpiano"]
            chant.lit_position = position_expander.get_text(row["Office"], row["Genre"], row["Position"])
            chant.manuscript = manuscript_list[0]
            chant.save()

            # Concordances
            for c in list(row["Concordances"]):
                matching_concordance = Concordance.objects.filter(letter_code=c)
                if matching_concordance:
                    chant.concordances.add(matching_concordance[0])

            # Tracking
            if (index % 100) == 0:
                self.stdout.write(u"{0} chants imported.".format(index))

        self.stdout.write(u"Successfully imported {0} chants into database.".format(index))
