import os
import os.path
from itertools import chain
import re

import pymei
from django.core.management.base import BaseCommand, make_option

from cantusdata.models.neume_exemplar import NeumeExemplar
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.folio import Folio


# It's pretty awful that we need to use tricks like this to work out what folio is what
FOLIO_REGEX = re.compile(r"_([a-z0-9]+)\.\w+$", re.IGNORECASE)


class DocumentManipulationException(Exception):
    pass


class Command(BaseCommand):
    """Automatically select exemplars for all neumes found in a manuscript"""

    option_list = BaseCommand.option_list + (
        make_option(
            "--use-specific",
            nargs=2,
            metavar="NEUME_NAME INDEX",
            help="Use the ith instance of the neume in the specified file as an exemplar (only works when "
            "given an MEI file, not a directory; index begins at 0)",
        ),
    )

    args = "manuscript_id file_or_directory"

    def handle(self, *args, **options):
        (ms_id, target) = args

        try:
            ms_id = int(ms_id)
        except (ValueError, TypeError):
            raise ValueError(
                "expected a manuscript id but got {!r}".format(ms_id)
            )

        # Get the manuscript object, primarily to ensure that it actually exists
        self.manuscript = Manuscript.objects.get(id=ms_id)

        # Exemplar
        self.exemplars = {
            exemplar.name: exemplar
            for exemplar in NeumeExemplar.objects.filter(
                folio__manuscript=self.manuscript
            )
        }

        if options["use_specific"]:
            if not os.path.isfile(target):
                self.stderr.write(
                    "--use-specific only works when given a specific MEI file"
                )
                return

            name, index = options["use_specific"]

            try:
                index = int(index)
            except (TypeError, ValueError):
                self.stderr.write(
                    "expected an integer but got {}".format(index)
                )
                return

            self.use_specific_exemplar(target, name, index)
            return

        if os.path.isdir(target):
            files = chain.from_iterable(
                (os.path.join(p, f) for f in fs)
                for (p, _, fs) in os.walk(target)
            )
            for file_path in files:
                self.find_exemplars(file_path)
        else:
            self.find_exemplars(target)

    def find_exemplars(self, file_path):
        try:
            folio_number, folio, doc = self.load_document(file_path)
        except DocumentManipulationException as e:
            self.stderr.write(e.message)
            return

        for neume in doc.getElementsByName("neume"):
            name_attr = neume.getAttribute("name")

            if not name_attr:
                continue

            name = name_attr.value

            if name in self.exemplars:
                continue

            try:
                self.save_exemplar(neume, name, folio_number, folio, doc)
            except DocumentManipulationException as e:
                self.stderr.write(e.message)
            else:
                self.stdout.write(
                    'using the first instance on folio {} for "{}"'.format(
                        folio_number, name
                    )
                )

    def use_specific_exemplar(self, file_path, desired_name, index):
        try:
            folio_number, folio, doc = self.load_document(file_path)
        except DocumentManipulationException as e:
            self.stderr.write(e.message)
            return

        instances_found = 0

        for neume in doc.getElementsByName("neume"):
            name_attr = neume.getAttribute("name")

            if not name_attr:
                continue

            name = name_attr.value

            if name != desired_name:
                continue

            if instances_found == index:
                old_exemplar = self.exemplars.get(desired_name)

                try:
                    self.save_exemplar(neume, name, folio_number, folio, doc)
                except DocumentManipulationException as e:
                    self.stderr.write(e.message)
                else:
                    if old_exemplar:
                        old_exemplar.delete()

                return
            else:
                instances_found += 1

        self.stderr.write(
            "could not get instance {} of neume {}: only {} instances found".format(
                index, desired_name, instances_found
            )
        )

    def save_exemplar(self, neume, name, folio_number, folio, doc):
        try:
            zone = get_zone(doc, neume.getAttribute("facs").value)
        except DocumentManipulationException as e:
            raise DocumentManipulationException(
                "failed to get zone for neume {}, folio {}: {}".format(
                    name, folio_number, e
                )
            )

        x = zone["ulx"]
        y = zone["uly"]
        width = zone["lrx"] - zone["ulx"]
        height = zone["lry"] - zone["uly"]

        exemplar = NeumeExemplar(
            name=name,
            folio=folio,
            x_coord=x,
            y_coord=y,
            width=width,
            height=height,
        )
        exemplar.save()

        self.exemplars[name] = exemplar

    def load_document(self, file_path):
        folio_number = get_folio(file_path)

        if folio_number is None:
            raise DocumentManipulationException(
                "could not identify folio for file {}".format(file_path)
            )

        try:
            folio = Folio.objects.get(
                number=folio_number, manuscript=self.manuscript
            )
        except Folio.DoesNotExist:
            raise DocumentManipulationException(
                "no folio with number {} in manuscript".format(folio_number)
            )
        except Folio.MultipleObjectsReturned:
            raise DocumentManipulationException(
                "multiple folios with number {} in manuscript...".format(
                    folio_number
                )
            )

        doc = pymei.documentFromFile(file_path, False).getMeiDocument()

        return folio_number, folio, doc


def get_folio(file_path):
    match = FOLIO_REGEX.search(file_path)

    if not match:
        return None

    return match.group(1)


def get_zone(doc, zone_id):
    zone = doc.getElementById(zone_id)

    if zone is None:
        raise DocumentManipulationException(
            "no element with id {} (expected a zone)".format(zone_id)
        )

    if zone.name != "zone":
        raise DocumentManipulationException(
            "expected #{} to be a zone but got {}".format(zone_id, zone.name)
        )

    attrs = {}

    for attr_name in ("ulx", "uly", "lrx", "lry"):
        attr = zone.getAttribute(attr_name)

        if attr is None:
            raise DocumentManipulationException(
                "no attr {} found for zone #{}".format(attr_name, zone)
            )

        try:
            value = int(attr.value)
        except (TypeError, ValueError):
            raise DocumentManipulationException(
                "non-integer value {!r} for attribute {}, zone #{}".format(
                    attr.value, attr_name, zone
                )
            )

        attrs[attr_name] = value

    return attrs
