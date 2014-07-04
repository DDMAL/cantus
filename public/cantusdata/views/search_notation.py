
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, JSONPRenderer

from cantusdata.helpers import search_utils
import solr
import json
import types
from operator import itemgetter

class SearchNotationView(APIView):

    def get(self, request, *args, **kwargs):

        q = request.GET.get('q', None)
        stype = request.GET.get('type', None)
        rows = request.GET.get("rows", "100")
        start = request.GET.get("start", "0")

        q_opt = {}
        if stype in ("neumes", "intervals"):
            q = q.replace(" ", "_")
        elif stype == 'pnames-invariant':
            stype = "pnames"
            q = ' OR '.join(search_utils.get_transpositions(q))
            q_opt = {"q_op": "OR"}

        query = "type:cantusdata_music_notation {0}:{1}".format(stype, q)
        # return Response(query)
        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        response = solrconn.query(query, sort="folio_t asc", rows=rows,
                                  start=start, **q_opt)

        # for i, obj in enumerate(response.results):
        #     print obj

        js = {"result": response.results, "num_found": response.numFound}

        return Response(js)


class LiberSearchException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)


class LiberSearchView(APIView):
    """
    Search algorithm copied over from the Liber Usualis code
    """

    def get(self, request, *args, **kwargs):

        q = request.GET.get('q', None)
        stype = request.GET.get('type', None)
        rows = request.GET.get("rows", "100")
        start = request.GET.get("start", "0")

        results = self.do_query(stype, q, 5, 5)

        return Response({'numFound': len(results), 'results': results})

    def do_query(self, qtype, query, zoom_level, max_zoom=4):

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        query = query.lower()

        if qtype == "neumes":
            query_stmt = 'neumes:{0}'.format(query.replace(' ', '_'))
        elif qtype == "pnames" or qtype == "pnames-invariant":
            if not search_utils.valid_pitch_sequence(query):
                raise LiberSearchException("The query you provided is not a valid pitch sequence")
            real_query = query if qtype == 'pnames' else ' OR '.join(search_utils.get_transpositions(query))

            print real_query

            query_stmt = 'pnames:{0}'.format(real_query)
        elif qtype == "contour":
            query_stmt = 'contour:{0}'.format(query)
        elif qtype == "text":
            query_stmt = 'text:"{0}"'.format(query)
        elif qtype == "intervals":
            query_stmt = 'intervals:{0}'.format(query.replace(' ', '_'))
        elif qtype == "incipit":
            query_stmt = "incipit:{0}*".format(query)
        else:
            raise LiberSearchException("Invalid query type provided")

        if qtype == "pnames-invariant":
            response = solrconn.query(query_stmt, score=False, sort="pagen asc", q_op="OR", rows=1000000)
        else:
            response = solrconn.query(query_stmt, score=False, sort="pagen asc", rows=1000000)
        numfound = response.numFound

        results = []
        boxes = []

        # get only the longest ngram in the results
        if qtype == "neumes":
            notegrams_num = search_utils.get_neumes_length(query)
            response = [r for r in response if len(r['pnames']) == notegrams_num]

        for d in response:
            page_number = d['pagen']
            locations = json.loads(d['location'].replace("'", '"'))

            if isinstance(locations, types.DictType):
                box_w = locations['width']
                box_h = locations['height']
                box_x = locations['ulx']
                box_y = locations['uly']
                boxes.append({'p': page_number, 'w': box_w, 'h': box_h, 'x': box_x, 'y': box_y})
            else:
                for location in locations:
                    box_w = location['width']
                    box_h = location['height']
                    box_x = location['ulx']
                    box_y = location['uly']
                    boxes.append({'p': page_number, 'w': box_w, 'h': box_h, 'x': box_x, 'y': box_y})

        zoom_diff = max_zoom - int(zoom_level)
        real_boxes = []
        for box in boxes:
            #incorporate zoom
            box['w'] = search_utils.incorporate_zoom(box['w'], zoom_diff)
            box['h'] = search_utils.incorporate_zoom(box['h'], zoom_diff)
            box['x'] = search_utils.incorporate_zoom(box['x'], zoom_diff)
            box['y'] = search_utils.incorporate_zoom(box['y'], zoom_diff)

            if box['w'] > 0 and box['h'] > 0:
                real_boxes.append(box)

        boxes_sorted = sorted(real_boxes, key=itemgetter('p', 'y'))

        return boxes_sorted