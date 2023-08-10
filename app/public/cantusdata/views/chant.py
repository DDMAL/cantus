from cantusdata.models.chant import Chant
from cantusdata.serializers.chant import ChantSerializer
from rest_framework import generics


class ChantList(generics.ListAPIView):
    model = Chant
    queryset = Chant.objects.all()
    serializer_class = ChantSerializer


class ChantDetail(generics.RetrieveAPIView):
    model = Chant
    queryset = Chant.objects.all()
    serializer_class = ChantSerializer
