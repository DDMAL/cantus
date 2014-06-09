from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from cantusdata.serializers.search import SearchSerializer
import solr


class ManuscriptFolioSetView(APIView):
    serializer_class = SearchSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)

    def get(self, request, *args, **kwargs):

        manuscript_id = kwargs['pk']

        composed_request = u'type:"cantusdata_folio" AND manuscript_id:{0}'.format(manuscript_id)

        if 'number' in kwargs:
            folio_number = kwargs['number']
            print folio_number
            composed_request = u'type:"cantusdata_folio" AND number:{0}'.format(folio_number)

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        result = solrconn.query(composed_request, sort="number asc",
                                rows=1000)
        return Response(result)