from cantusdata.models.folio import Folio
from cantusdata.serializers.folio import FolioSerializer
from rest_framework import generics


class FolioList(generics.ListCreateAPIView):
    model = Folio
    queryset = Folio.objects.all()
    serializer_class = FolioSerializer


class FolioDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Folio
    queryset = Folio.objects.all()
    serializer_class = FolioSerializer
