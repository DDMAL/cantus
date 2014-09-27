from django.core.management.base import BaseCommand
from django.utils.text import slugify

import csv
from neumeeditor.models.style import Style
from neumeeditor.models.name import Name
from neumeeditor.models.glyph import Glyph


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        self.import_csv_file("ccnames.csv", "Salzinnes")

    def import_csv_file(self, file_name, style_name):
        csv_file = csv.DictReader(open("data_dumps/glyphs/" + str(file_name)))
        # Get the style object
        style = Style.objects.get(name=str(style_name))
        index = 0
        for row in csv_file:
            glyph = Glyph.objects.create(style=style,
                                         short_code=str(row["short_code"]))
            Name.objects.create(string=str(row["name"]),
                                glyph=glyph)
            index += 1

        self.stdout.write(
            u"Successfully imported {0} glyphs into database.".format(index))
