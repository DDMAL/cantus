from django.core.management.base import BaseCommand
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
from django.core.management import call_command
from django.db import transaction
import csv


class Command(BaseCommand):
    """
    Import a folio mapping (CSV file)
    Save that mapping to both django and Solr (through signals)
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--manuscripts",
            action="store",
            nargs="+",
            dest="manuscript_ids",
            help="Identifies manuscripts being mapped. Provided in same order as --mapping_data",
        )
        parser.add_argument(
            "--mapping_data",
            action="store",
            nargs="+",
            dest="mapping_data",
            help="""Two possibilities can be passed in this argument. First, a list of file names of csvs 
            that contain mapping data in same order as the --manuscripts argument. Second, a list
            containing mapping data in the same order as the --manuscripts argument. Each item in the list
            is a list of dictionaries with keys "folio" and "uri." The latter option is most 
            useful when calling from the call_command function, rather than the command line.""",
        )
        parser.add_argument(
            "--no-refresh",
            action="store_false",
            dest="refresh",
            default=True,
            help="Do not refresh Solr after the import",
        )
        parser.add_argument(
            "--path",
            action="store",
            dest="csvs_path",
            default="data_dumps/folio_mapping",
            help="Directory where mapping_data csvs are found. Defaults to ./data_dumps/folio_mapping",
        )

        parser.add_argument(
            "--task",
            dest="task",
            help="Optional argument used when called from the django admin interface. Passes asynchronous task.",
        )

    @transaction.atomic
    def handle(self, *args, **options):

        manuscript_ids = options["manuscript_ids"]
        manuscript_mapping_dict = dict(zip(manuscript_ids, options["mapping_data"]))
        task = options.get("task", None)

        for manuscript_id in manuscript_ids:
            input_data = manuscript_mapping_dict[manuscript_id]

            # Query database for manuscript id.
            try:
                manuscript = Manuscript.objects.get(id=manuscript_id)
            except IOError:
                raise IOError(f"Manuscript {manuscript_id} does not exist")

            # If input_data is a string, it should be a csv file name
            # where mapping data is persisted. Attempt to read it.
            # If input_data is a list, it should be the mapping data itself.
            if isinstance(input_data, str):
                try:
                    mapping_data = csv.DictReader(
                        open(f"{options['csvs_path']}/{input_data}", "r")
                    )
                except IOError:
                    raise IOError(
                        f"File {options['csvs_path']}/{input_data} does not exist"
                    )
            elif isinstance(input_data, list):
                mapping_data = input_data

            self.stdout.write(f"Starting import process for manuscript {manuscript_id}")

            # Iterate through rows in the mapping_data.
            for index, row in enumerate(mapping_data):
                folio = row["folio"]
                uri = row["uri"]

                # Save in the Django DB
                try:
                    folio_obj = Folio.objects.get(
                        number=folio, manuscript__id=manuscript_id
                    )
                except Folio.DoesNotExist:
                    # If no folio is found, create one
                    folio_obj = Folio()
                    folio_obj.number = folio
                    folio_obj.manuscript = manuscript

                folio_obj.image_uri = uri
                folio_obj.save()

                if task:
                    task.update_state(state="STARTED", meta={"folios_imported": index})
                if index > 0 and index % 50 == 0:
                    self.stdout.write(f"Imported {index} folios")

            manuscript.save()

            self.stdout.write(
                f"All folios of manuscript {manuscript_id} have been imported"
            )

        # Refreshing Solr chants is necessary since chants have a field image_uri
        # which is used when clicking on a search result. Folio records in solr
        # are already updated during the database saving process through the solr_sync
        # signal, but chant records are not because no interaction occurs with the chant
        # object in the database.
        if options["refresh"]:
            self.stdout.write("Refreshing Solr chants after folio import")
            call_command(
                "refresh_solr", record_type="chants", manuscript_ids=manuscript_ids
            )
        else:
            self.stdout.write(
                "Import process completed. To refresh Solr,"
                "use './manage.py refresh_solr chants [manuscript_id ...]'"
            )
        for manuscript_id in manuscript_ids:
            manuscript = Manuscript.objects.get(id=manuscript_id)
            manuscript.is_mapped = "MAPPED"
            manuscript.save()
