from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from django.core.management import call_command
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
import urllib
import json
import csv
import re
import threading


class MapFoliosView(APIView):

    template_name = "admin/map_folios.html"
    renderer_classes = (TemplateHTMLRenderer, )

    def get(self, request, *args, **kwargs):
        # Return the URIs and folio names
        if 'manifest' not in request.GET or 'data' not in request.GET or 'manuscript_id' not in request.GET:
            return Response()

        manuscript_id = request.GET['manuscript_id']
        manifest = request.GET['manifest']
        data = request.GET['data']


        uris = []
        manifest_json = urllib.urlopen(manifest)
        manifest_data = json.load(manifest_json)

        for canvas in manifest_data['sequences'][0]['canvases']:
            service = canvas['images'][0]['resource']['service']
            uri = service['@id']
            path_tail = 'default.jpg' if service['@context'] == 'http://iiif.io/api/image/2/context.json' else 'native.jpg'
            uris.append({
                'full': uri,
                'thumbnail': uri + '/full/,160/0/' + path_tail,
                'large': uri + '/full/,1800/0/' + path_tail,
                'short': re.sub(r'^.*/(?!$)', '', uri)
            })

        folios = []
        with open('./data_dumps/' + data) as data_csv:
            data_contents = csv.DictReader(data_csv)

            for rownum, row in enumerate(data_contents):
                folio = row['Folio']

                if rownum > 0 and folios[len(folios) - 1] == folio:
                    continue

                folios.append(folio)

        return Response({'uris': uris, 'folios': folios, 'manuscript_id': manuscript_id})

    def post(self, request):
        try:
            thread = threading.Thread(target=_save_mapping, args=(request, ), kwargs={})
            thread.start()
        except Exception as e:
                return Response({'error': e})

        return Response({'posted': True})


def _save_mapping(request):
    # Add stuff in Solr if POST arguments
    # A file dump should also be created so that Solr can be refreshed

    manuscript_id = request.POST['manuscript_id']
    manuscript = Manuscript.objects.get(id=manuscript_id)
    data = [['folio', 'uri']] # CSV column headers

    for index, value in request.POST.iteritems():
        # 'index' should be the uri, and 'value' the folio name
        if index == 'csrfmiddlewaretoken' or index == 'manuscript_id' or len(value) == 0:
            continue

        # Save in the Django DB
        try:
            folio_obj = Folio.objects.get(number=value, manuscript__id=manuscript_id)
        except Folio.DoesNotExist:
            # If no folio is found, create one
            folio_obj = Folio()
            folio_obj.number = value
            folio_obj.manuscript = manuscript

        folio_obj.image_uri = index
        folio_obj.save()

        # Data to be saved in a CSV file
        data.append([value, index])

    # Save in a data dump
    with open('./data_dumps/folio_mapping/{0}.csv'.format(manuscript_id), 'w') as dump_csv:
        csv_writer = csv.writer(dump_csv)
        csv_writer.writerows(data)

    # Refresh all chants in solr after the folios have been updated
    call_command('refresh_solr', 'chants', str(manuscript_id))
