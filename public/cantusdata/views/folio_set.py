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

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        manuscript_id = kwargs['pk']

        if 'number' in kwargs:
            folio_number = kwargs['number']
            composed_request =\
                u'type:"cantusdata_folio" AND manuscript_id:{0} AND number:{1}'\
                .format(manuscript_id, folio_number.lower())
            result = solrconn.query(composed_request, sort="number asc",
                        rows=1)
            # We only want the single result!
            # TODO: Figure out the best way to handle this
            if (result.results):
                return Response(result.results[0])
            else:
                return Response(result)
        else:
            composed_request = u'type:"cantusdata_folio" AND manuscript_id:{0}'\
            .format(manuscript_id)
            result = solrconn.query(composed_request, sort="number asc",
                                rows=1000)
            return Response(result)
