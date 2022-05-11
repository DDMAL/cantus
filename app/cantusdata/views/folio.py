from cantusdata.models.folio import Folio
from cantusdata.serializers.folio import FolioSerializer
from django.http import Http404
from rest_framework import generics


class FolioList(generics.ListCreateAPIView):
    model = Folio
    serializer_class = FolioSerializer

    # Give a way to find a specific folio with query params
    def get_queryset(self):
        queryset = Folio.objects.all()

        number = self.request.query_params.get("number", None)
        manuscript = self.request.query_params.get("manuscript", None)

        if number is None or manuscript is None:
            return queryset

        # Use a regex to ignore leading zeros
        queryset = queryset.filter(
            number__iregex=r"^0*{}$".format(number), manuscript__id=manuscript
        )

        if len(queryset) == 0:
            raise Http404("No data for a folio with that number")
        else:
            return queryset[:1]  # Make sure we return only one element


class FolioDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Folio
    queryset = Folio.objects.all()
    serializer_class = FolioSerializer
