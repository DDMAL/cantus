from django.conf import settings
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from cantusdata.serializers.search import SearchSerializer
from cantusdata.helpers.strip_solr_metadata import strip_solr_metadata
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
                .format(manuscript_id, folio_number)
            result = solrconn.query(composed_request, sort="number asc",
                        rows=1)
            # We only want the single result!
            # TODO: Figure out the best way to handle this
            if (result.results):
                return Response(strip_solr_metadata(result.results[0]))
            else:
                raise Http404("No data for a folio with that number")
        else:
            composed_request = u'type:"cantusdata_folio" AND manuscript_id:{0}'\
            .format(manuscript_id)
            results = solrconn.query(composed_request, sort="number asc",
                                rows=1000)
            return Response([strip_solr_metadata(result) for result in results])
