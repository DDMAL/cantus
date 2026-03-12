"""
Management command to set the viewer warning for manuscripts with incompatible manifests.
"""

from django.core.management.base import BaseCommand
from cantusdata.models.manuscript import Manuscript


class Command(BaseCommand):
    help = "Set viewer warnings for manuscripts with incompatible manifest versions"

    def handle(self, *args, **options):
        # Update Salzinnes manuscript with incompatible manifest warning
        salzinnes = Manuscript.objects.filter(
            manifest_url="https://lib.is/IE9434868/manifest"
        ).first()

        if salzinnes:
            salzinnes.viewer_warning = (
                "This manuscript's manifest is currently using an old presentation version "
                "and is not compatible with our viewer. A fix is in progress; until then, "
                "this manuscript cannot be viewed here."
            )
            salzinnes.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated warning for manuscript: {salzinnes}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("Salzinnes manuscript not found in database")
            )
