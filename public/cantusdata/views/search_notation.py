from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response

from cantusdata.helpers import search_utils
import solr
import json
import types
from operator import itemgetter


class NotationException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)


class SearchNotationView(APIView):
    """
    Search algorithm copied over from the Liber Usualis code
    """

    def get(self, request, *args, **kwargs):

        q = request.GET.get('q', None)
        stype = request.GET.get('type', None)
        manuscript = request.GET.get('manuscript', None)
        rows = request.GET.get("rows", "100")
        start = request.GET.get("start", "0")

        try:
            results = self.do_query(manuscript, stype, q, 5, 5)
        except Exception as e:
            # Something went wrong in the search
            print "Exception: {0}".format(e)
            # So we want an empty list to avoid server error 500
            results = []

        return Response({'numFound': len(results), 'results': results})

    def do_query(self, manuscript, qtype, query, zoom_level, max_zoom=4):
        # This will be appended to the search query so that we only get
        # data from the manuscript that we want!
        manuscript_query = ' AND siglum_slug:\"{0}\"'.format(manuscript)

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        query = query.lower()

        if qtype == "neumes":
            query_stmt = 'neumes:{0}'.format(
                # query
                query.replace(' ', '_')
            )
        elif qtype == "pnames" or qtype == "pnames-invariant":
            if not search_utils.valid_pitch_sequence(query):
                raise NotationException("The query you provided is not a valid pitch sequence")
            real_query = query if qtype == 'pnames' else ' OR '.join(search_utils.get_transpositions(query))
            query_stmt = 'pnames:{0}'.format(real_query)
        elif qtype == "contour":
            query_stmt = 'contour:{0}'.format(query)
        elif qtype == "text":
            query_stmt = 'text:{0}'.format(query)
        elif qtype == "intervals":
            query_stmt = 'intervals:{0}'.format(query.replace(' ', '_'))
        elif qtype == "incipit":
            query_stmt = "incipit:{0}*".format(query)
        else:
            raise NotationException("Invalid query type provided")

        if qtype == "pnames-invariant":
            print query_stmt + manuscript_query
            response = solrconn.query(query_stmt + manuscript_query,
                                      score=False, sort="folio asc", q_op="OR",
                                      rows=1000000)
        else:
            print query_stmt + manuscript_query
            response = solrconn.query(query_stmt + manuscript_query,
                                      score=False, sort="folio asc",
                                      rows=1000000)
        numfound = response.numFound

        results = []
        boxes = []

        # get only the longest ngram in the results
        if qtype == "neumes":
            if manuscript == "ch-sgs-390":
                pass
            else:
                notegrams_num = search_utils.get_neumes_length(query)
                response = [r for r in response if len(r['pnames']) == notegrams_num]

        for d in response:
            page_number = d['folio']
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