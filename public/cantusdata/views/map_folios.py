from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from django.core.management import call_command
from django.db import transaction
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
import urllib
import json
import csv
import re
import threading
import pdb

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
        
        uri_list = [uri['full'] for uri in uris]
        uri_list_ids = _extract_ids(uri_list)

        folios = []
        folio_imagelink = {}
        with open('./data_dumps/' + data) as data_csv:
            data_contents = csv.DictReader(data_csv)
            for row in data_contents:
                folio = row['Folio']
                link = row['Image link']
                if folio not in folios:
                    folios.append(folio)
                if link != '' and folio not in folio_imagelink:
                    folio_imagelink[folio] = link
        
        imagelinks = list(folio_imagelink.values())
        imagelinks_ids = _extract_ids(imagelinks)
        folio_imagelink = dict(zip(imagelinks_ids, folio_imagelink.keys())
        print(folio_imagelink)

        return Response({'uris': uris, 'folios': folios, 'manuscript_id': manuscript_id})

    def post(self, request):
        try:
            thread = threading.Thread(target=_save_mapping, args=(request, ), kwargs={})
            thread.start()
        except Exception as e:
            return Response({'error': e})

        return Response({'posted': True})


def _extract_ids(str_list):
    tmp_str_list = _remove_longest_common_string(str_list, 'left')
    print(tmp_str_list)
    tmp_str_list = _remove_longest_common_string(tmp_str_list, 'right')
    print(tmp_str_list)
    return tmp_str_list


def _remove_longest_common_string(str_list, align='left'):
    longest_str = max(str_list, key=len)
    max_length = len(longest_str)
    if align == 'left':
        norm_str_list = [s.ljust(max_length) for s in str_list]
    elif align == 'right':
        norm_str_list = [s.rjust(max_length) for s in str_list]    
    s1 = norm_str_list[0]
    diffs = []
    for s2 in norm_str_list[1:]:
        [diffs.append(i) for i in range(max_length) if s1[i] != s2[i]]
    diffs_set = set(diffs)
    print(diffs_set)
    mismatch_start = min(diffs_set)
    mismatch_end = max(diffs_set)
    return [s[mismatch_start:mismatch_end+1].strip() for s in norm_str_list]




@transaction.atomic
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
