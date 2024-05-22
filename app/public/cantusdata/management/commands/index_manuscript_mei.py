from typing import Any, Dict
from os import path, listdir

from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings
from cantusdata.helpers.mei_processing.mei_tokenizer import MEITokenizer
from cantusdata.models.folio import Folio

from solr.core import SolrConnection  # type: ignore

MEI4_DIR = path.join("/code", "production-mei-files")


class Command(BaseCommand):
    help = (
        "This command indexes the contents of MEI files in Solr, using"
        "the MEITokenizer class to extract n-grams from the MEI files."
        "Files must be named in the format [some string]_[folio number].mei."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "manuscript_id",
            type=int,
            nargs=1,
            help=(
                "The ID of the manuscript whose MEI data should be indexed."
                "Must have MEI files in a subdirectory of the --mei-dir argument"
                "named with this ID."
            ),
        )
        parser.add_argument(
            "--mei-dir",
            type=str,
            default=MEI4_DIR,
            help=(
                "The directory containing the MEI files to be indexed."
                "Defaults to '/code/production-mei-files'."
            ),
        )
        parser.add_argument(
            "--min-ngram",
            type=int,
            default=1,
            help="The minimum n-gram length to index from the MEI files.",
        )
        parser.add_argument(
            "--max-ngram",
            type=int,
            default=5,
            help="The maximum n-gram length to index from the MEI files.",
        )
        parser.add_argument(
            "--flush-index",
            action="store_true",
            help=(
                "If this flag is set, the command will delete all existing OMR"
                "documents for the specified manuscript before indexing the new data."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        solr_conn = SolrConnection(settings.SOLR_SERVER)
        manuscript_id = options["manuscript_id"][0]
        if options.get("flush_index"):
            self.flush_manuscript_ngrams_from_index(solr_conn, manuscript_id)
        else:
            folio_map: Dict[str, str] = dict(
                Folio.objects.filter(manuscript_id=manuscript_id).values_list(
                    "number", "image_uri"
                )
            )
            if not folio_map:
                raise ValueError(f"No folios found for manuscript {manuscript_id}.")
            manuscript_mei_path = path.join(options["mei_dir"], str(manuscript_id))
            if not path.exists(manuscript_mei_path):
                raise FileNotFoundError(f"--mei-dir path does not exist.")
            manuscript_mei_files = [
                f for f in listdir(manuscript_mei_path) if f.endswith(".mei")
            ]
            if len(manuscript_mei_files) == 0:
                raise FileNotFoundError(f"No MEI files found in {manuscript_mei_path}.")
            for mei_file in manuscript_mei_files:
                folio_number: str = mei_file.split("_")[-1].split(".")[0]
                if not folio_number in folio_map:
                    raise ValueError(
                        f"Folio number {folio_number} in MEI file {mei_file} does not exist in the database."
                    )
                tokenizer = MEITokenizer(
                    path.join(manuscript_mei_path, mei_file),
                    min_ngram=options["min_ngram"],
                    max_ngram=options["max_ngram"],
                )
                ngram_docs = tokenizer.create_ngram_documents()
                for doc in ngram_docs:
                    doc["manuscript_id"] = manuscript_id
                    doc["folio"] = folio_number
                    doc["image_uri"] = folio_map.get(folio_number, "")
                solr_conn.add_many(ngram_docs)
                solr_conn.commit()

    def flush_manuscript_ngrams_from_index(
        self, solr_conn: SolrConnection, manuscript_id: int
    ) -> None:
        """
        Deletes all n-gram documents for a given manuscript from the Solr index.
        """
        solr_conn.delete_query(f"type:omr_ngram AND manuscript_id:{manuscript_id}")
        solr_conn.commit()
