from neumeeditor.helpers.authentication import ExpiringTokenAuthentication
from neumeeditor.models.name_nomenclature_membership import NameNomenclatureMembership
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from neumeeditor.serializers.name_nomenclature_membership import NameNomenclatureMembershipSerializer


class NameNomenclatureMembershipList(generics.ListCreateAPIView):
    model = NameNomenclatureMembership
    serializer_class = NameNomenclatureMembershipSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
    queryset = NameNomenclatureMembership.objects.all()
    # authentication_classes = (ExpiringTokenAuthentication,
    #                           SessionAuthentication)
    # permission_classes = (IsAuthenticated,)


class NameNomenclatureMembershipDetail(generics.RetrieveUpdateDestroyAPIView):
    model = NameNomenclatureMembership
    serializer_class = NameNomenclatureMembershipSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
    queryset = NameNomenclatureMembership.objects.all()
    # authentication_classes = (SessionAuthentication,)
    # permission_classes = (IsAuthenticated,)
