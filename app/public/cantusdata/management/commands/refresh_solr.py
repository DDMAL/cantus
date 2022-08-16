from django.core.management.base import BaseCommand
from cantusdata.models.chant import Chant
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.folio import Folio
from cantusdata import settings
import solr


class Command(BaseCommand):

    TYPE_MAPPING = {
        "manuscripts": Manuscript,
        "chants": Chant,
        "folios": Folio,
    }

    help = f"""Refreshes solr index associated with a specific manuscript for a specific type.
        \n\t Usage: ./manage.py refresh_solr --record_type {"|".join(list(TYPE_MAPPING.keys()))} [--manuscript_ids manuscript_id ...]
        \n\t Specify manuscript ID(s) to only refresh selected items in that/those manuscript(s)
        \n\t Use --all_types to refresh all {len(TYPE_MAPPING)} types."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--record_type",
            action="store",
            nargs=1,
            choices=["manuscripts", "chants", "folios"],
            dest="record_type",
            help=f"Type of records to refresh. Choose from {list(self.TYPE_MAPPING.keys())}",
        )
        parser.add_argument(
            "--manuscript_ids",
            action="store",
            nargs="*",
            default="all_manuscripts",
            dest="manuscript_ids",
            help="Manuscripts for which solr should be refreshed.",
        )
        parser.add_argument(
            "--all_types",
            action="store_true",
            dest="all",
            default=False,
            help=f"Refresh all types: {list(self.TYPE_MAPPING.keys())}",
        )

    def handle(self, *args, **options):
        solr_conn = solr.SolrConnection(settings.SOLR_SERVER)
        # Parse arguments
        manuscript_ids = options["manuscript_ids"]
        types = []
        if options["all"]:
            record_types = list(self.TYPE_MAPPING.keys())
        else:
            record_types = [options["record_type"]]

        for record_type in record_types:
            # Remove the trailing 's' to make the type singular
            type_singular = record_type.rstrip("s")
            model = self.TYPE_MAPPING[record_type]

            self.stdout.write(f"Flushing {type_singular} data...")

            if manuscript_ids == "all_manuscripts":
                # Create delete query for all manuscripts
                delete_query = f"type:cantusdata_{type_singular}"
            else:
                # Create delete query for some manuscripts if specific manuscripts are specified.
                # Create string of the form: "( MAN_ID1 OR MAN_ID2 OR ... )"
                formatted_ids = "(" + " OR ".join(manuscript_ids) + ")"
                if model == Manuscript:
                    delete_query = (
                        f"type:cantusdata_{type_singular} AND item_id:{formatted_ids}"
                    )
                else:
                    delete_query = f"type:cantusdata_{type_singular} AND manuscript_id:{formatted_ids}"

            solr_conn.delete_query(delete_query)

            self.stdout.write(
                f"Re-adding {type_singular} data... (may take a few minutes)"
            )

            if manuscript_ids == "all_manuscripts":
                objects = model.objects.all()
            else:
                if model == Manuscript:
                    objects = model.objects.filter(id__in=manuscript_ids)
                else:
                    objects = model.objects.filter(manuscript__id__in=manuscript_ids)

            solr_records = []
            nb_obj = len(objects)
            for index, object in enumerate(objects):
                solr_records.append(object.create_solr_record())

                # Adding by blocks prevents out of memory errors
                if (index > 0 and index % 500 == 0) or (index == nb_obj - 1):
                    self.stdout.write(f"{index + 1} / {nb_obj}")
                    solr_conn.add_many(solr_records)
                    solr_records = []

        self.stdout.write("Committing changes...")
        solr_conn.commit()
        self.stdout.write("Done!")
