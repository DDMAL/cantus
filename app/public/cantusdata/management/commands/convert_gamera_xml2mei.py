import os.path
import optparse

from django.core.management.base import BaseCommand

from cantusdata.helpers.gamera_xml2mei.converter import (
    initializeArgumentParser,
    main,
)


BASE_NAME = os.path.basename(os.path.splitext(__file__)[0])


class Command(BaseCommand):
    # FIXME: we can use add_arguments and remove help and option_list once we upgrade to Django 1.8

    args = "[in_dir [out_dir]]"

    option_list = BaseCommand.option_list + (
        optparse.make_option(
            "--dump-zone-clusters",
            action="store_true",
            help="write a visualization of the zone clusters to file",
        ),
        optparse.make_option(
            "--dump-zone-overlay",
            nargs=2,
            metavar="TIFF",
            help="create a copy of the TIFF image with the zones overlaid",
        ),
    )

    def add_arguments(self, parser):
        initializeArgumentParser(parser)

    def handle(self, *args, **options):
        # FIXME: argparse will handle positional arguments in Django 1.8
        input_dir = "."
        output_dir = "."

        if len(args) >= 1:
            input_dir = args[0]

            if len(args) == 2:
                output_dir = args[1]

            elif len(args) > 2:
                raise ValueError(
                    "{} accepts no more than 2 positional arguments".format(
                        BASE_NAME
                    )
                )

        # Fake an argparse-style arguments object
        class HelperArgs(object):
            input_directory = input_dir
            output_directory = output_dir
            dump_zone_clusters = options["dump_zone_clusters"]
            dump_zone_overlay = options["dump_zone_overlay"]

            # Some processing like this may be necessary in Django 1.8
            verbose = options["verbosity"] not in ("0", "1")

        main(args=HelperArgs())