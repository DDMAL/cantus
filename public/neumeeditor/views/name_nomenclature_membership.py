from rest_framework.response import Response
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


class NameNomenclatureMembershipListForGlyph(generics.ListAPIView):
    serializer_class = NameNomenclatureMembershipSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)

    def get_queryset(self, glyph_id):
        return NameNomenclatureMembership.objects.filter(glyph=glyph_id)

    def get(self, request, *args, **kwargs):
        glyph_id = kwargs['pk']
        # We want to get all chants of a particular folio of a particular
        # manuscript.  It is fastest to pull these from Solr!
        serializer = self.serializer_class(self.get_queryset(glyph_id),
                                           many=True,
                                           context={'request': request})
        return Response(serializer.data)
