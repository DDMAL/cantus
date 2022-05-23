from django.core.management.base import BaseCommand
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        id = 0
        for item in Manuscript.objects.all():
            self.stdout.write("Reindexing manuscript {0}.".format(id))
            item.save()
            id += 1
        id = 0
        for item in Folio.objects.all():
            self.stdout.write("Reindexing folio {0}.".format(id))
            item.save()
            id += 1
        id = 0
        for item in Chant.objects.all():
            self.stdout.write("Reindexing chant {0}.".format(id))
            item.save()
            id += 1
