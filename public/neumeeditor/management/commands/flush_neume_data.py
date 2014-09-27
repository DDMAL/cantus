from django.core.management.base import BaseCommand
from django.utils.text import slugify

import csv
from neumeeditor.models.style import Style
from neumeeditor.models.name import Name
from neumeeditor.models.glyph import Glyph
from neumeeditor.models.image import Image

from django.core.management import call_command


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        # call_command('syncdb', interactive=True)
        # Destroy names
        Name.objects.all().delete()
        print "Names destroyed."
        # Destroy images
        Image.objects.all().delete()
        print "Image destroyed."
        # Destroy glyphs
        Glyph.objects.all().delete()
        print "Glyphs destroyed."
        # Destroy styles
        Style.objects.all().delete()
        print "Styles destroyed."
