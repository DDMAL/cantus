from cantusdata.models import Concordance
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        """
        """
        file = open("data_dumps/" + str(args[0]))
        # Nuke the db concordances
        Concordance.objects.all().delete()
        # Every line is a new concordance
        for line in file.readlines():
            # This method is pretty hacky, but it seems to work
            concordance = Concordance()

            concordance.letter_code = line.split(" ", 1)[0]
            line = line.split(" ", 1)[1]

            concordance.institution_city = line.split(",", 1)[0]
            line = line.split(",", 1)[1]

            concordance.institution_name = line.split(",", 1)[0]
            line = line.split(",", 1)[1]

            concordance.sections = line.split(" (", 1)[0]
            line = line.split(" (", 1)[1]

            concordance.date = line.split(", from", 1)[0]
            line = line.split(", from", 1)[1]

            concordance.location = line.split(")", 1)[0]
            line = line.split(")", 1)[1]

            line = line.split(": ", 1)[1]

            concordance.rism_code = line.split("]", 1)[0]

            concordance.save()
