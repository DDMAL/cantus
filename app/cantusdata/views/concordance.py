from cantusdata.models.concordance import Concordance
from cantusdata.serializers.concordance import ConcordanceSerializer
from rest_framework import generics


class ConcordanceList(generics.ListCreateAPIView):
    model = Concordance
    queryset = Concordance.objects.all()
    serializer_class = ConcordanceSerializer


class ConcordanceDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Concordance
    queryset = Concordance.objects.all()
    serializer_class = ConcordanceSerializer
