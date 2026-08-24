from typing import Any, Dict, Optional
from os import path, listdir
import re

from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings
from solr.core import SolrConnection  # type: ignore[import-untyped]

from cantusdata.helpers.mei_processing.mei_tokenizer import MEITokenizer
from cantusdata.models.folio import Folio

MEI4_DIR = path.join("/code", "production-mei-files")
FOLIO_NUMBER_REGEX = re.compile(r"[a-zA-Z]?\d+[a-z]?")


def escape_solr_phrase(value: str) -> str:
    """
    Escape a value being interpolated into a quoted Solr phrase.

    Only the backslash and the double quote mean anything inside quotes, and the
    backslash has to go first or it would escape the escapes added after it.

    Folio numbers currently reach this as either an operator's --folio argument
    or a Folio.number read back from the database, so none of them contain a
    quote today. That is a property of the data rather than a guarantee, and the
    query built from it is a *delete*: a stray quote would end the phrase early
    and leave the rest of the folio number as loose query syntax, against an
    index whose contents are then removed. Cheaper to escape than to rely on
    every folio number that ever reaches the database being well behaved.
    """
    return value.replace("\\", "\\\\").replace('"', '\\"')


class Command(BaseCommand):
    help = (
        "This command indexes the contents of MEI files in Solr, using"
        "the MEITokenizer class to extract n-grams from the MEI files."
        "Files must be named in the format [some string]_[folio number].mei,"
        "where [folio number] is an optional single letter followed by "
        "some number of digits followed by an optional"
        "lowercase single letter. The command currently has a workaround for folios "
        "that have MEI files but are NOT in CantusDB. See #891 for details "
        "about how to handle this case -- the command will alert the user "
        "when it encounters this case."
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
                "documents for the specified manuscript."
            ),
        )
        parser.add_argument(
            "--folio",
            type=str,
            default=None,
            help=(
                "Restrict the command to a single folio, given by its number "
                "(e.g. '001r'). Only the MEI file for that folio is indexed, and "
                "--flush-index/--replace only delete that folio's documents."
            ),
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help=(
                "Delete the existing OMR documents for the folios about to be "
                "indexed before indexing them. Without this flag, indexing a folio "
                "that is already indexed leaves both sets of documents in the index. "
                "Combine with --folio to replace a single folio."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        solr_conn = SolrConnection(settings.SOLR_SERVER)
        manuscript_id = options["manuscript_id"][0]
        folio_filter: Optional[str] = options.get("folio")
        if options.get("flush_index"):
            self.flush_manuscript_ngrams_from_index(
                solr_conn, manuscript_id, folio=folio_filter
            )
            return None
        folio_map: Dict[str, str] = dict(
            Folio.objects.filter(manuscript_id=manuscript_id).values_list(  # type: ignore[arg-type]
                "number", "image_uri"
            )
        )
        if not folio_map:
            raise ValueError(f"No folios found for manuscript {manuscript_id}.")
        manuscript_mei_path = path.join(options["mei_dir"], str(manuscript_id))
        if not path.exists(manuscript_mei_path):
            raise FileNotFoundError("--mei-dir path does not exist.")
        manuscript_mei_files = [
            f for f in listdir(manuscript_mei_path) if f.endswith(".mei")
        ]
        if len(manuscript_mei_files) == 0:
            raise FileNotFoundError(f"No MEI files found in {manuscript_mei_path}.")
        self.reject_duplicate_folio_files(manuscript_mei_path, manuscript_mei_files)
        if folio_filter is not None:
            manuscript_mei_files = [
                f
                for f in manuscript_mei_files
                if f.split("_")[-1].split(".")[0] == folio_filter
            ]
            if len(manuscript_mei_files) == 0:
                raise FileNotFoundError(
                    f"No MEI file for folio {folio_filter} found in "
                    f"{manuscript_mei_path}."
                )
        if options.get("replace"):
            if folio_filter is None:
                self.warn_about_whole_manuscript_replace(
                    solr_conn,
                    manuscript_id,
                    manuscript_mei_path,
                    len(manuscript_mei_files),
                )
            self.flush_manuscript_ngrams_from_index(
                solr_conn, manuscript_id, folio=folio_filter
            )
        for mei_file in manuscript_mei_files:
            folio_number: str = mei_file.split("_")[-1].split(".")[0]
            if not FOLIO_NUMBER_REGEX.match(folio_number):
                raise ValueError(
                    f"Folio number {folio_number} in MEI file {mei_file}"
                    "does not exist in the database."
                )
            if not folio_number in folio_map or folio_map[folio_number] == "":
                self.stdout.write(
                    self.style.WARNING(
                        f"Folio number {folio_number} in MEI file "
                        f"{mei_file} did not exist in the database. Creating record. "
                        "See #891 for details on how to handle this case."
                    )
                )
                Folio.objects.create(manuscript_id=manuscript_id, number=folio_number)
            tokenizer = MEITokenizer(
                path.join(manuscript_mei_path, mei_file),
                min_ngram=options["min_ngram"],
                max_ngram=options["max_ngram"],
            )
            ngram_docs = tokenizer.create_ngram_documents()
            for doc in ngram_docs:
                doc["manuscript_id"] = manuscript_id
                doc["folio"] = folio_number
                # `or ""` because Folio.image_uri is nullable: a None here would
                # be dropped by Solr, leaving the document without the field.
                doc["image_uri"] = folio_map.get(folio_number) or ""
            solr_conn.add_many(ngram_docs)
            solr_conn.commit()
        return None

    def flush_manuscript_ngrams_from_index(
        self,
        solr_conn: SolrConnection,
        manuscript_id: int,
        folio: Optional[str] = None,
    ) -> None:
        """
        Deletes n-gram documents for a given manuscript from the Solr index.

        Deletes every n-gram of the manuscript unless `folio` is given, in which
        case only that folio's n-grams are deleted. The folio number is matched
        exactly: `folio` is a Solr string field.
        """
        query = f"type:omr_ngram AND manuscript_id:{manuscript_id}"
        if folio is not None:
            query += f' AND folio:"{escape_solr_phrase(folio)}"'
        solr_conn.delete_query(query)
        solr_conn.commit()

    def reject_duplicate_folio_files(
        self, manuscript_mei_path: str, mei_files: list[str]
    ) -> None:
        """
        Refuse to run when two MEI files in the directory name the same folio.

        The folio comes from the segment after the last underscore, so files with
        different prefixes -- a curated "CDN-Hsmu_M2149.L4_034r.mei" beside a
        "cdn-hsmu-m2149l4_034r.mei" -- both describe folio 034r and would each
        contribute a full set of n-grams for it, doubling that folio's results
        even with --replace. There should be exactly one file per folio.
        """
        by_folio: Dict[str, list[str]] = {}
        for mei_file in mei_files:
            folio = mei_file.split("_")[-1].split(".")[0]
            by_folio.setdefault(folio, []).append(mei_file)
        duplicates = {
            folio: names for folio, names in by_folio.items() if len(names) > 1
        }
        if duplicates:
            detail = "; ".join(
                f"{folio}: {', '.join(sorted(names))}"
                for folio, names in sorted(duplicates.items())
            )
            raise ValueError(
                f"{manuscript_mei_path} holds more than one MEI file for the same "
                f"folio ({detail}). Indexing would count those folios more than "
                "once; remove the duplicates first."
            )

    def warn_about_whole_manuscript_replace(
        self,
        solr_conn: SolrConnection,
        manuscript_id: int,
        manuscript_mei_path: str,
        mei_file_count: int,
    ) -> None:
        """
        Report how much of the index a whole-manuscript --replace is about to rebuild.

        --replace without --folio deletes every n-gram of the manuscript and then
        rebuilds only from the files in a single --mei-dir. If that directory does
        not hold every folio of the manuscript, coverage silently shrinks, so print
        the numbers that make that visible.
        """
        indexed = solr_conn.query(
            "*:*", fq=f"type:omr_ngram AND manuscript_id:{manuscript_id}", rows=0
        )
        self.stdout.write(
            self.style.WARNING(
                f"--replace will delete all {indexed.numFound} indexed n-gram "
                f"document(s) for manuscript {manuscript_id} and rebuild them from "
                f"the {mei_file_count} MEI file(s) in {manuscript_mei_path}. "
                "If that directory does not contain every folio of this manuscript, "
                "the missing folios will no longer be searchable. Use --folio to "
                "replace a single folio instead."
            )
        )
