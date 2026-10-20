import re

from cantusdata.models.folio import Folio
from cantusdata.pagination import ListPagination
from cantusdata.serializers.folio import FolioSerializer
from django.http import Http404
from rest_framework import generics


class FolioList(generics.ListAPIView):
    model = Folio
    serializer_class = FolioSerializer
    pagination_class = ListPagination

    def _lookup_params(self):
        """(number, manuscript) when the request looks up one folio, else None."""
        number = self.request.query_params.get("number", None)
        manuscript = self.request.query_params.get("manuscript", None)
        if number is None or manuscript is None:
            return None
        return number, manuscript

    # Give a way to find a specific folio with query params
    def get_queryset(self):
        lookup = self._lookup_params()
        if lookup is None:
            return Folio.objects.order_by("manuscript_id", "number", "pk")
        number, manuscript = lookup
        if not manuscript.isdigit():
            raise Http404("No data for a folio with that number")

        # Use a regex to ignore leading zeros. The number is escaped: it goes
        # into a database regex, where `(` alone is an error.
        queryset = Folio.objects.filter(
            number__iregex=r"^0*{}$".format(re.escape(number.strip())),
            manuscript__id=int(manuscript),
        )

        if len(queryset) == 0:
            raise Http404("No data for a folio with that number")
        else:
            return queryset[:1]  # Make sure we return only one element

    def paginate_queryset(self, queryset):
        # A lookup answers with a plain one-element list, which the viewer
        # reads as response[0] (DivaView.js).
        if self._lookup_params() is not None:
            return None
        return super().paginate_queryset(queryset)


class FolioDetail(generics.RetrieveAPIView):
    model = Folio
    queryset = Folio.objects.all()
    serializer_class = FolioSerializer
