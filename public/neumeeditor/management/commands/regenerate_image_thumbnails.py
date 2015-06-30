import csv
from django.core.management.base import BaseCommand
from neumeeditor.models.image import Image


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        # Re-save every image, thereby regenerating all thumbnails
        for image in Image.objects.all():
            image.save()
