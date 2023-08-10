from cantusdata.models.concordance import Concordance
from cantusdata.serializers.concordance import ConcordanceSerializer
from rest_framework import generics


class ConcordanceList(generics.ListAPIView):
    model = Concordance
    queryset = Concordance.objects.all()
    serializer_class = ConcordanceSerializer


class ConcordanceDetail(generics.RetrieveAPIView):
    model = Concordance
    queryset = Concordance.objects.all()
    serializer_class = ConcordanceSerializer
