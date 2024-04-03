from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.request import Request

from cantusdata.helpers import search_utils
from solr.core import SolrConnection  # type: ignore
import json
from typing import Any, Tuple, List, Dict, Union
from operator import itemgetter


class NotationException(APIException):
    status_code = 400
    default_detail = "Notation search request invalid"


class SearchNotationView(APIView):
    """
    Search algorithm adapted from the Liber Usualis code
    """

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        q = request.GET.get("q", None)
        stype = request.GET.get("type", None)
        manuscript = request.GET.get("manuscript", None)

        if q and stype and manuscript:
            results, numFound = self.do_query(manuscript, stype, q)
        else:
            results = []

        return Response({"numFound": numFound, "results": results})

    def do_query(
        self, manuscript: str, qtype: str, query: str
    ) -> Tuple[List[Dict[str, Union[str, List[str]]]], int]:
        # This will be appended to the search query so that we only get
        # data from the manuscript that we want!
        manuscript_query = " AND manuscript_id:{0}".format(manuscript)

        solrconn = SolrConnection(settings.SOLR_SERVER)

        # Normalize case and whitespace
        query = " ".join(elem for elem in query.lower().split())

        if qtype == "neume_names":
            query_stmt = "neume_names:{0}".format(
                # query
                query.replace(" ", "_")
            )
        elif qtype == "pitch_names" or qtype == "pnames-invariant":
            # TODO: Implement a pitch validity check and
            # transposition for pitch names
            # if not search_utils.valid_pitch_sequence(query):
            #     raise NotationException(
            #         "The query you provided is not a valid pitch sequence"
            #     )
            # real_query = (
            #     query
            #     if qtype == "pnames"
            #     else " OR ".join(search_utils.get_transpositions(query))
            # )
            formatted_query = "_".join(query.split())
            query_stmt = f"pitch_names:({formatted_query})"
        elif qtype == "contour":
            formatted_query = "_".join(query.split())
            query_stmt = f"contour:{formatted_query}"
        elif qtype == "text":
            query_stmt = "text:{0}".format(query)
        elif qtype == "intervals":
            query_stmt = f"intervals:{query.replace(' ', '_')}"
        elif qtype == "incipit":
            query_stmt = "incipit:{0}*".format(query)
        else:
            raise NotationException("Invalid query type provided")

        if qtype == "pnames-invariant":
            print(query_stmt + manuscript_query)
            response = solrconn.query(
                query_stmt + manuscript_query,
                score=False,
                sort="folio asc",
                q_op="OR",
                rows=1000000,
            )
        else:
            print(query_stmt + manuscript_query)
            response = solrconn.query(
                query_stmt + manuscript_query,
                score=False,
                sort="folio asc",
                rows=100,
            )

        results = []

        box_sort_key = itemgetter("p", "y")

        for d in response:
            image_uri = d["image_uri"]
            folio = d["folio"]
            locations = json.loads(d["location"].replace("'", '"'))

            if isinstance(locations, dict):
                box_w = locations["width"]
                box_h = locations["height"]
                box_x = locations["ulx"]
                box_y = locations["uly"]
                boxes = [
                    {
                        "p": image_uri,
                        "f": folio,
                        "w": box_w,
                        "h": box_h,
                        "x": box_x,
                        "y": box_y,
                    }
                ]
            else:
                boxes = []

                for location in locations:
                    box_w = location["width"]
                    box_h = location["height"]
                    box_x = location["ulx"]
                    box_y = location["uly"]
                    boxes.append(
                        {
                            "p": image_uri,
                            "f": folio,
                            "w": box_w,
                            "h": box_h,
                            "x": box_x,
                            "y": box_y,
                        }
                    )

                boxes.sort(key=box_sort_key)

            if qtype == "neume_names":
                results.append(
                    {
                        "boxes": boxes,
                        "contour": d["contour"].split("_"),
                        "neumes": d["neume_names"].split("_"),
                        "pnames": d["pitch_names"].split("_"),
                        "semitones": [int(x) for x in d["semitones"].split("_")],
                    }
                )
            else:
                results.append(
                    {
                        "boxes": boxes,
                        "contour": d["contour"].split("_"),
                        "pnames": d["pitch_names"].split("_"),
                        "semitones": [int(x) for x in d["semitones"].split("_")],
                    }
                )

        results.sort(key=lambda result: [box_sort_key(box) for box in result["boxes"]])

        return results, response.numFound


# def get_value(d, key, transform):
#     try:
#         value = d[key]
#     except KeyError:
#         return None

#     return transform(value)
