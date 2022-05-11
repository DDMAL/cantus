from django.core.management.base import BaseCommand
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        # Get the manuscript
        try:
            input_id = input("Please enter a manuscript id: ")
            id = int(input_id)
        except ValueError:
            self.stdout.write("Error: {0} is not an integer!".format(input_id))
            return
        try:
            manuscript = Manuscript.objects.get(id=id)
        except:
            self.stdout.write(
                "Error: Manuscript with id={0} does not exist.".format(id)
            )
            return
        # Reindex the folios
        index = 0
        for folio in Folio.objects.filter(manuscript=manuscript):
            self.stdout.write("Reindexing folio {0}.".format(index))
            folio.save()
            index += 1
        index = 0
        for chant in Chant.objects.filter(manuscript=manuscript):
            self.stdout.write("Reindexing chant {0}.".format(index))
            chant.save()
            index += 1
        self.stdout.write("{0} reindexed.".format(manuscript.name))
