from typing import Any, List
from os import path, listdir

from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings
from solr.core import SolrConnection  # type: ignore

from cantusdata.helpers.mei_processing.mei_tokenizer import MEITokenizer, NgramDocument
from cantusdata.models.folio import Folio

MEI4_DIR = path.join(settings.BASE_DIR, "data_dumps", "mei4")


class Command(BaseCommand):
    help = (
        "This command indexes the contents of MEI files in Solr, using"
        "the MEITokenizer class to extract n-grams from the MEI files."
        "NOTE: This command currently requires that MEI files be transferred"
        "to the Docker container manually (to a folder in the data_dumps/mei4"
        "directory with the manuscript ID as the folder name) and that the"
        "files are named with a '*_[folio number].mei' suffix where [folio number]"
        "matches the 'number' attribute of the Folio model. Additional development"
        "is anticipated to make this process more robust."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "manuscript_id",
            type=int,
            nargs=1,
            help=(
                "The ID of the manuscript whose MEI data should be indexed."
                "Must have MEI files in the data_dumps/mei4/[manuscript_id] directory."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        solr_conn = SolrConnection(settings.SOLR_SERVER)
        manuscript_id = str(options["manuscript_id"][0])
        # Delete any existing OMR documents for this manuscript
        solr_conn.delete_query(f"type:omr_ngram AND manuscript_id:{manuscript_id}")
        solr_conn.commit()
        folio_map = dict(
            Folio.objects.filter(manuscript_id=manuscript_id).values_list(
                "number", "image_uri"
            )
        )
        manuscript_mei_path = path.join(MEI4_DIR, manuscript_id)
        manuscript_mei_files = [
            f for f in listdir(manuscript_mei_path) if f.endswith(".mei")
        ]
        for mei_file in manuscript_mei_files:
            folio_number: str = mei_file.split("_")[-1].split(".")[0]
            tokenizer = MEITokenizer(
                path.join(manuscript_mei_path, mei_file), min_ngram=1, max_ngram=5
            )
            ngram_docs = tokenizer.get_ngram_documents()
            for doc in ngram_docs:
                doc["manuscript_id"] = manuscript_id
                doc["folio"] = folio_number
                doc["image_uri"] = folio_map.get(folio_number, "")
            solr_conn.add_many(ngram_docs)
            solr_conn.commit()
