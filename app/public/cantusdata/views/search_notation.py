from typing import Any, TypedDict, Union, Optional, NotRequired

import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import APIException

from cantusdata.helpers.search_utils import validate_query, get_transpositions

RETURNED_FIELDS = [
    "manuscript_id",
    "folio",
    "image_uri",
    "pitch_names",
    "contour",
    "semitone_intervals",
    "neume_names",
    "location_json",
]


class SolrQueryResultItem(TypedDict):
    manuscript_id: int
    folio: str
    image_uri: str
    pitch_names: str
    contour: str
    semitone_intervals: str
    neume_names: str
    location_json: list[dict[str, int]]


class NotationSearchResultItem(TypedDict):
    boxes: list[dict[str, Union[int, str]]]
    contour: list[str]
    semitones: list[str]
    pnames: list[str]
    neumes: NotRequired[list[str]]


class NotationSearchException(APIException):
    status_code = 400
    default_detail = "Notation search request invalid."


class SearchNotationView(APIView):
    """
    Search algorithm adapted from the Liber Usualis code
    """

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        q = request.GET.get("q", None)
        stype = request.GET.get("type", None)
        manuscript_param = request.GET.get("manuscript", None)
        rows_param = request.GET.get("rows", "100")
        start_param = request.GET.get("start", "0")

        # Do some parameter validation and cast to appropriate types
        if not q or not stype or not manuscript_param:
            raise NotationSearchException("Missing required parameters.")
        if not rows_param.isdigit() or not start_param.isdigit():
            raise NotationSearchException("'Rows' and 'Start' must be integers.")
        if not manuscript_param.isdigit():
            raise NotationSearchException("Manuscript ID must be digits.")
        rows = int(rows_param)
        start = int(start_param)
        manuscript_id = int(manuscript_param)

        query_str = self.create_query_string(q, stype)
        results, num_found = self.do_query(manuscript_id, query_str, rows, start)

        return Response({"numFound": num_found, "results": results})

    def create_query_string(self, q: str, q_type: str) -> str:
        """
        Format the query and query type into a string for solr.
        """
        normalized_q_elems = q.lower().split()
        q_valid = validate_query(normalized_q_elems, q_type)
        if not q_valid:
            raise NotationSearchException("Invalid query.")
        if q_type == "pitch_names_invariant":
            transpositions = get_transpositions(normalized_q_elems)
            # Create a query string for the tranpositions:
            # e.g. if transpositions are [["a", "b" , "c"], "b","c","d"], etc.]
            # then the query string will be:
            # "(a_b_c OR b_c_d OR etc.)"
            q_str = " OR ".join(
                "_".join(pitch for pitch in transposition)
                for transposition in transpositions
            )
            q_str = f"({q_str})"
            q_type = "pitch_names"
        else:
            q_str = "_".join(normalized_q_elems)
        return f"{q_type}:{q_str}"

    def create_boxes(
        self, locations: list[dict[str, int]], image_uri: str, folio: str
    ) -> list[dict[str, Union[int, str]]]:
        boxes: list[dict[str, Union[int, str]]] = []
        for location in locations:
            boxes.append(
                {
                    "p": image_uri,
                    "f": folio,
                    "w": location["width"],
                    "h": location["height"],
                    "x": location["ulx"],
                    "y": location["uly"],
                }
            )
        return boxes

    def do_query(
        self, manuscript_id: int, q_str: str, rows: int, start: int
    ) -> tuple[list[NotationSearchResultItem], int]:
        # Add type and manuscript parameters to the query string
        query_str_w_manuscript = (
            f"type:omr_ngram AND manuscript_id:{manuscript_id} AND {q_str}"
        )
        complete_query_str = (
            f"{settings.SOLR_SERVER}/select?q=*:*&fq={query_str_w_manuscript}"
            f"&fl={','.join(RETURNED_FIELDS)}&sort=folio+asc&rows={rows}&start={start}"
        )
        response = requests.get(complete_query_str, timeout=10).json()
        request_results: list[SolrQueryResultItem] = response["response"]["docs"]
        num_found = response["response"]["numFound"]
        results = []
        for d in request_results:
            boxes = self.create_boxes(d["location_json"], d["image_uri"], d["folio"])
            result: NotationSearchResultItem = {
                "boxes": boxes,
                "contour": d["contour"].split("_"),
                "semitones": d["semitone_intervals"].split("_"),
                "pnames": d["pitch_names"].split("_"),
            }
            neume_names: Optional[str] = d.get("neume_names")
            if neume_names:
                neume_names_list = neume_names.split("_")
                result["neumes"] = neume_names_list
            results.append(result)

        return results, num_found
