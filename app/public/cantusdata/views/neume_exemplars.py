from typing import Any, Tuple, List, TypedDict, Optional, Unpack, cast

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.conf import settings
from django.views.generic import TemplateView
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
import requests
from requests import Response as RequestsResponse

from cantusdata.models import Manuscript, NeumeExemplar
from cantusdata.models.neume_exemplar import EXEMPLAR_IMAGE_SIDE_LENGTH
from cantusdata.helpers.iiif_helpers import construct_image_api_url
from cantusdata.serializers.neume_exemplar import NeumeExemplarSerializer


class NeumeExemplarAPIKwargs(TypedDict):
    pk: int
    neume_name: str


class NeumeData(TypedDict):
    neume_count: int
    current_neume_exemplar: Optional[str]


class NeumeSetItem(TypedDict):
    neume_name: str
    folio: str
    image_url: str


class NeumeSetAPIView(APIView):
    """
    An API that accepts GET requests to fetch potential neume exemplars in
    a manuscript.

    The API accepts a `neume_name` parameter which determines the type of
    neume to fetch exemplars for. If no `neume_name` is provided, all neumes are
    returned. It also accepts a `start` parameter which
    is passed on to the Solr query to determine the index of the first result
    to return and a `rows` parameter which determines the number of results
    to return. The `start` and `rows` parameters are optional and default to
    0 and 10 respectively.
    """

    # Settings for padding around the neume exemplar bounding box (used in the
    # calculate_exemplar_box method).
    PADDING_TOP = 60
    PADDING_BOTTOM = 45
    PADDING_LEFT = 45
    PADDING_RIGHT = 45

    def get(
        self, request: Any, *args: Any, **kwargs: Unpack[NeumeExemplarAPIKwargs]
    ) -> Response:
        """
        Handles a get request to the pick neume exemplars view.
        """
        response_dict: dict[str, Any] = {}
        q_manuscript_id = kwargs["pk"]
        q_neume_name = request.GET.get("neume_name", "")
        q_start = request.GET.get("start", 0)
        q_rows = request.GET.get("rows", 10)
        try:
            exemplars = self._fetch_potential_exemplars(
                q_manuscript_id, q_neume_name, start=q_start, rows=q_rows
            )
        except requests.exceptions.RequestException as e:
            response_dict["solr_request_error"] = str(e)
            return Response(response_dict, status=500)
        response_dict["neume_name"] = q_neume_name
        response_dict["manuscript"] = q_manuscript_id
        response_dict["start"] = q_start
        response_dict["neume_exemplars"] = exemplars
        response_dict["exemplar_image_side_length"] = EXEMPLAR_IMAGE_SIDE_LENGTH
        return Response(response_dict)

    def _fetch_potential_exemplars(
        self,
        manuscript_id: int,
        neume_name: str,
        start: int,
        rows: int,
    ) -> List[NeumeSetItem]:
        """
        Get potential exemplars of a neume type in a manuscript.

        Args:
            manuscript: The manuscript object for which exemplars are being fetched.
            neume_name: The name of the neume type for which exemplars are being fetched.
            start: The index of the first result to return.
            rows: The number of results to return.

        Returns:
            A list of tuples containing the neume name, the folio, and image URL of each
            potential exemplar.
        """
        params: dict[str, str | int] = {
            "q": "*:*",
            # If no neume names are provided, filter by "neume_names:*
            # AND NOT neume_names:*_* to get ngrams where the neume_names
            # field exists but is a single-neume ngram.
            "fq": f"manuscript_id:{manuscript_id} AND type:omr_ngram"
            + (
                f" AND neume_names:{neume_name}"
                if neume_name
                else " AND neume_names:* AND NOT neume_names:*_*"
            ),
            "rows": rows,
            "sort": "folio asc",
            "start": start,
            "fl": "*",
        }
        response: RequestsResponse = requests.get(
            f"{settings.SOLR_SERVER}/select", timeout=10, params=params
        )
        response.raise_for_status()
        results_json = response.json()["response"]
        if results_json["numFound"] > 0:
            exemplars: List[NeumeSetItem] = []
            for result in results_json["docs"]:
                # Since we're dealing with single-neume ngrams in this
                # result, we know each location will be a list with only
                # a single bounding box (single neumes don't span multiple
                # systems).
                location = result["location_json"][0]
                ulx, uly, width, height = self.calculate_exemplar_box(
                    location["ulx"],
                    location["uly"],
                    location["width"],
                    location["height"],
                )
                image_url = construct_image_api_url(
                    result["image_uri"],
                    region=(f"{ulx},{uly},{width},{height}"),
                    size=f"{EXEMPLAR_IMAGE_SIDE_LENGTH},",
                )
                exemplars.append(
                    {
                        "neume_name": neume_name,
                        "folio": result["folio"],
                        "image_url": image_url,
                    }
                )
            return exemplars
        return []

    def calculate_exemplar_box(
        self, ulx: int, uly: int, width: int, height: int
    ) -> Tuple[int, int, int, int]:
        """
        Given the bounding box coordinates of a neume in the MEI file, calculate
        the coordinates of a box that will contain the neume and some extra
        space around it (for the neume exemplar image) and be a square.
        """
        width_with_padding = width + self.PADDING_LEFT + self.PADDING_RIGHT
        height_with_padding = height + self.PADDING_TOP + self.PADDING_BOTTOM
        ulx -= self.PADDING_LEFT
        uly -= self.PADDING_TOP
        # If the width is greater than the height, we'll make the box square
        # by adding padding to the top and bottom.
        if width_with_padding > height_with_padding:
            height_padding_for_square = (width_with_padding - height_with_padding) // 2
            uly -= height_padding_for_square
            height_with_padding = width_with_padding
        # If the height is greater than the width, we'll make the box square
        # by adding padding to the left and right.
        elif height_with_padding > width_with_padding:
            width_padding_for_square = (height_with_padding - width_with_padding) // 2
            ulx -= width_padding_for_square
            width_with_padding = height_with_padding
        return ulx, uly, width_with_padding, height_with_padding


class NeumeExemplarsAPIView(ListModelMixin, GenericAPIView):  # type: ignore[type-arg]
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = NeumeExemplarSerializer

    def get_queryset(self) -> QuerySet[NeumeExemplar]:
        manuscript_id = self.kwargs["pk"]
        return (
            Manuscript.objects.get(pk=manuscript_id)
            .neume_exemplars.select_related("folio", "folio__manuscript")
            .all()
        )

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.list(request, *args, **kwargs)

    def post(self, request: Request, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Create a neume exemplar from a POST request to the API.
        """
        data = request.data.copy()
        # Remove the CSRF token from the request data
        data.pop("csrfmiddlewaretoken", None)
        exemplars_to_save = []
        for neume_name, iiif_url in data.items():
            parsed_exemplar_dict = self._parse_iiif_url(iiif_url)
            parsed_exemplar_dict["name"] = neume_name
            exemplars_to_save.append(parsed_exemplar_dict)
        existing_exemplars = self.get_queryset()
        if existing_exemplars.exists():
            serializer = self.get_serializer(
                instance=existing_exemplars, data=exemplars_to_save, many=True
            )
        else:
            serializer = self.get_serializer(data=exemplars_to_save, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        messages.success(request, "Neume exemplars saved successfully.")
        return redirect(
            reverse("admin:cantusdata_manuscript_change", args=[self.kwargs["pk"]])
        )

    def _parse_iiif_url(self, iiif_url: str) -> dict[str, str | int]:
        split_url = iiif_url.split("/")
        region_param = split_url[-4]
        region = region_param.split(",")
        x, y, w, h = map(int, region)
        p = "/".join(split_url[:-4])
        return {"p": p, "x": x, "y": y, "w": w, "h": h}


class PickNeumeExemplarsView(TemplateView):
    template_name = "admin/pick_neume_exemplars.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["manuscript"] = Manuscript.objects.get(pk=kwargs["pk"])
        ngrams_indexed = self.check_indexed_mei(context["manuscript"])
        if not ngrams_indexed:
            context["ngrams_indexed"] = False
            return context
        existing_exemplars = self.get_existing_exemplar_links(context["manuscript"])
        neume_name_counts = self.get_neume_name_counts(context["manuscript"])
        neume_data: dict[str, NeumeData] = {}
        for neume_name, neume_count in neume_name_counts.items():
            neume_data[neume_name] = {
                "neume_count": neume_count,
                "current_neume_exemplar": existing_exemplars.get(neume_name),
            }
        context["ngrams_indexed"] = ngrams_indexed
        context["neume_data"] = neume_data
        return context

    def get_existing_exemplar_links(self, manuscript: Manuscript) -> dict[str, str]:
        """
        Gets the existing neume examplars for a manuscript, if any,
        and returns a dictionary with the neume name as the key
        and the examplar image URL as the value.
        """
        exemplar_image_dict: dict[str, str] = {}
        for exemplar in manuscript.neume_exemplars.select_related("folio").all():
            neume_name = exemplar.name
            image_uri = exemplar.folio.image_uri
            assert (
                image_uri is not None
            )  # we know that the image_uri of a folio with a neume exemplar is not None
            exemplar_image_url = construct_image_api_url(
                image_uri,
                region=f"{exemplar.x_coord},{exemplar.y_coord},{exemplar.width},{exemplar.height}",
                size=f"{EXEMPLAR_IMAGE_SIDE_LENGTH},",
            )
            exemplar_image_dict[neume_name] = exemplar_image_url
        return exemplar_image_dict

    def check_indexed_mei(self, manuscript: Manuscript) -> bool:
        """
        Check if the manuscript has indexed MEI.
        """
        params: dict[str, str | int] = {
            "q": f"manuscript_id:{manuscript.pk} AND type:omr_ngram",
            "rows": 1,
        }
        omr_ngram_request = requests.get(
            f"{settings.SOLR_SERVER}/select",
            params=params,
            timeout=10,
        )
        omr_ngram_request.raise_for_status()
        num_omr_ngrams_found: int = omr_ngram_request.json()["response"]["numFound"]
        return num_omr_ngrams_found > 0

    def get_neume_name_counts(self, manuscript: Manuscript) -> dict[str, int]:
        """
        Get the neume names that exist in a manuscript and their counts.

        Args:
            manuscript: The manuscript for which neume names are being fetched.

        Returns:
            A dictionary of neume names and their counts.
        """
        params: dict[str, str | int] = {
            "q": "*:*",
            "fq": f"manuscript_id:{manuscript.pk} AND type:omr_ngram AND -neume_names:*_*",
            "rows": 0,
            "facet": "true",
            "facet.field": "neume_names",
            "facet.mincount": 1,
        }
        omr_ngram_request = requests.get(
            f"{settings.SOLR_SERVER}/select",
            params=params,
            timeout=10,
        )
        omr_ngram_request.raise_for_status()
        # Facets are returned as a list of alternating neume names and counts.
        neume_names: list[str | int] = omr_ngram_request.json()["facet_counts"][
            "facet_fields"
        ]["neume_names"]
        neume_name_counts: dict[str, int] = {}
        for i in range(0, len(neume_names), 2):
            neume_name = cast(str, neume_names[i])
            count = cast(int, neume_names[i + 1])
            neume_name_counts[neume_name] = count
        return neume_name_counts
