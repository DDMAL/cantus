import json
from typing import Any, NamedTuple, TypedDict, Union

import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import APIException

from cantusdata.helpers.search_utils import normalize_search_text
from cantusdata.views.search_notation import SearchNotationView

# text_general indexes n-grams of at most 15 characters, so a longer query
# word can never match. Its first 15 characters still match as a prefix.
MAX_QUERY_WORD_LENGTH = 15


class TextFields(NamedTuple):
    """The Solr fields searched for one way of normalizing text"""

    line: str
    next: str
    window: str


# Fields indexed by MEITokenizer.create_text_line_documents, keyed by whether
# syllables are joined (hyphens ignored) or separated.
TEXT_FIELDS = {
    True: TextFields("text_line_t", "text_next_t", "text_window_t"),
    False: TextFields("text_line_syl_t", "text_next_syl_t", "text_window_syl_t"),
}


class TextSearchResultItem(TypedDict):
    boxes: list[dict[str, Union[int, str]]]
    lines: list[str]


class TextSearchException(APIException):
    status_code = 400
    default_detail = "Text search request invalid."


class SearchMEITextView(APIView):
    """
    Search the lines of text encoded in a manuscript's MEI files (e.g. OCR'd
    text), as indexed by index_manuscript_mei. A line matches when it contains
    every word of the query, compared after normalize_search_text.

    Optional parameters:
        hyphens: "ignore" (default) joins syllables split by hyphens; "keep"
            matches them as separate syllables, as printed.
        multiline: "true" lets the words continue onto the next line, in
            which case a result may span two lines; "false" (default) does not.
    """

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        q = request.GET.get("q", None)
        manuscript_param = request.GET.get("manuscript_id", None)
        rows_param = request.GET.get("rows", "100")
        start_param = request.GET.get("start", "0")
        hyphens_param = request.GET.get("hyphens", "ignore")
        multiline_param = request.GET.get("multiline", "false")

        if not q or not manuscript_param:
            raise TextSearchException("Missing required parameters.")
        if not rows_param.isdigit() or not start_param.isdigit():
            raise TextSearchException("'Rows' and 'Start' must be integers.")
        if not manuscript_param.isdigit():
            raise TextSearchException("Manuscript ID must be digits.")
        if hyphens_param not in ("ignore", "keep"):
            raise TextSearchException("'Hyphens' must be 'ignore' or 'keep'.")
        if multiline_param not in ("true", "false"):
            raise TextSearchException("'Multiline' must be 'true' or 'false'.")
        join_syllables = hyphens_param == "ignore"
        multiline = multiline_param == "true"

        words = self.get_query_words(q, join_syllables)
        results, num_found = self.do_query(
            int(manuscript_param),
            words,
            join_syllables,
            multiline,
            int(rows_param),
            int(start_param),
        )
        return Response({"numFound": num_found, "results": results})

    def get_query_words(self, q: str, join_syllables: bool) -> list[str]:
        """
        Normalize the user's query into the words to search for. Normalization
        leaves only [a-z0-9] words, so nothing needs escaping for Solr.
        """
        words = [
            word[:MAX_QUERY_WORD_LENGTH]
            for word in normalize_search_text(q, join_syllables).split()
        ]
        if not words:
            raise TextSearchException("Invalid query.")
        return words

    def create_query_string(
        self, words: list[str], join_syllables: bool, multiline: bool
    ) -> str:
        """
        Build a Solr query requiring every word.

        A multi-line search matches a line together with the next one. To list
        each match once, a line only matches this way when the next line does
        not have every word by itself; that match is listed at the next line.
        """
        fields = TEXT_FIELDS[join_syllables]

        def all_words_in(field: str) -> str:
            return " AND ".join(f"{field}:{word}" for word in words)

        if not multiline:
            return all_words_in(fields.line)
        return (
            f"{all_words_in(fields.window)} AND "
            f"(({all_words_in(fields.line)}) OR (*:* -({all_words_in(fields.next)})))"
        )

    def do_query(
        self,
        manuscript_id: int,
        words: list[str],
        join_syllables: bool,
        multiline: bool,
        rows: int,
        start: int,
    ) -> tuple[list[TextSearchResultItem], int]:
        line_field = TEXT_FIELDS[join_syllables].line
        q_str = self.create_query_string(words, join_syllables, multiline)
        params: dict[str, Union[str, int]] = {
            "q": "*:*",
            "fq": f"type:mei_text_line AND manuscript_id:{manuscript_id} AND ({q_str})",
            "fl": ",".join(
                [
                    "folio",
                    "image_uri",
                    "location_json",
                    "text_line_stored",
                    "next_text_line_stored",
                    "next_location_stored",
                    line_field,
                ]
            ),
            "sort": "folio asc, line_order_i asc",
            "rows": rows,
            "start": start,
        }
        response = requests.get(
            f"{settings.SOLR_SERVER}/select", params=params, timeout=10
        ).json()
        results: list[TextSearchResultItem] = []
        for d in response["response"]["docs"]:
            image_uri = d.get("image_uri", "")
            result: TextSearchResultItem = {
                "boxes": SearchNotationView.create_boxes(
                    d["location_json"], image_uri, d["folio"]
                ),
                "lines": [d["text_line_stored"]],
            }
            # A multi-line match that the line can't account for by itself
            # continues onto the next line, so show that line too.
            if (
                multiline
                and "next_text_line_stored" in d
                and not self.has_all_words(d[line_field], words)
            ):
                result["boxes"] += SearchNotationView.create_boxes(
                    json.loads(d["next_location_stored"]), image_uri, d["folio"]
                )
                result["lines"].append(d["next_text_line_stored"])
            results.append(result)
        return results, response["response"]["numFound"]

    @staticmethod
    def has_all_words(normalized_text: str, words: list[str]) -> bool:
        """
        Whether normalized text matches every query word, the way Solr matches
        text_general fields here: a query word matches any indexed word
        containing it.
        """
        indexed_words = normalized_text.split()
        return all(
            any(word in indexed_word for indexed_word in indexed_words)
            for word in words
        )
