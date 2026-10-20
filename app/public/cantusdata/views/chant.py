from cantusdata.models.chant import Chant
from cantusdata.pagination import ListPagination
from cantusdata.serializers.chant import ChantSerializer
from rest_framework import generics


class ChantList(generics.ListAPIView):
    model = Chant
    # By pk: the model's ordering (sequence) repeats across manuscripts, which
    # would let rows move between pages.
    queryset = Chant.objects.order_by("pk")
    serializer_class = ChantSerializer
    pagination_class = ListPagination


class ChantDetail(generics.RetrieveAPIView):
    model = Chant
    queryset = Chant.objects.all()
    serializer_class = ChantSerializer
