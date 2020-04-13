from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from django.core.management import call_command
from django.db import transaction
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
import urllib.request, urllib.parse, urllib.error
import json
import csv
import re
import threading

class MapFoliosView(APIView):
    template_name = "admin/map_folios.html"
    renderer_classes = (TemplateHTMLRenderer, )
    def get(self, request, *args, **kwargs):
        # Return the URIs and folio names
        if 'manuscript_id' not in request.GET:
            manuscripts = Manuscript.objects.filter(manifest_url__isnull=False, public=True)
            manuscript_ids = [(m.id, str(m)) for m in manuscripts]
            return Response({'manuscript_ids': manuscript_ids})

        manuscript_id = int(request.GET['manuscript_id'])
        manuscript_obj = Manuscript.objects.get(id=manuscript_id)
        manifest = manuscript_obj.manifest_url

        uris_objs = []
        uris = []
        manifest_json = urllib.request.urlopen(manifest)
        manifest_data = json.loads(manifest_json.read().decode('utf-8'))
        for canvas in manifest_data['sequences'][0]['canvases']:
            service = canvas['images'][0]['resource']['service']
            uri = service['@id']
            uris.append(uri)
            path_tail = 'default.jpg' if service['@context'] == 'http://iiif.io/api/image/2/context.json' else 'native.jpg'
            uris_objs.append({
                'full': uri,
                'thumbnail': uri + '/full/,160/0/' + path_tail,
                'large': uri + '/full/,1800/0/' + path_tail,
                'short': re.sub(r'^.*/(?!$)', '', uri)
            })

        uri_ids = _extract_ids(uris)

        folios = []
        folio_imagelink = {}
        folios_query = Folio.objects.filter(manuscript__id=manuscript_id)
        for folio in folios_query:
            folios.append(folio.number)
            if folio.image_link:
                folio_imagelink[folio.number] = folio.image_link

        imagelinks = list(folio_imagelink.values())
        imagelinks_ids = _extract_ids(imagelinks)
        imagelink_folio = dict(list(zip(imagelinks_ids, list(folio_imagelink.keys()))))

        for idx, uri in enumerate(uris_objs):
            uri['id'] = uri_ids[idx]
            uri['folio'] = None
            if uri['id'] in imagelink_folio:
                uri['folio'] = imagelink_folio[uri['id']]

        return Response({'uris': uris_objs, 'folios': folios, 'manuscript_id': manuscript_id})

    def post(self, request):
        try:
            thread = threading.Thread(target=_save_mapping, args=(request, ), kwargs={})
            thread.start()
        except Exception as e:
            return Response({'error': e})

        return Response({'posted': True})


def _extract_ids(str_list):
    # string a: $OME/EXAMPLE/CR4ZY/STRING/123anid!!SOMEMOREIDENTICALSTUFF
    # string b: $OME/EXAMPLE/CR4ZY/STRING/123anotherid!!SOMEMOREIDENTICALSTUFF
    left_sweep = _remove_longest_common_string(str_list, 'left')
    # string a: anid!!SOMEMOREIDENTICALSTUFF
    # string b: anotherid!!SOMEMOREIDENTICALSTUFF
    right_sweep = _remove_longest_common_string(left_sweep, 'right')
    # string a: anid
    # string b: anotherid
    ids = [_remove_number_padding(s) for s in right_sweep]
    return ids

def _remove_longest_common_string(str_list, align='left'):
    longest_str = max(str_list, key=len)
    max_length = len(longest_str)
    if align == 'left':
        norm_str_list = [s.ljust(max_length) for s in str_list]
    elif align == 'right':
        norm_str_list = [s.rjust(max_length) for s in str_list]
    s1 = norm_str_list[0]
    diffs_set = set()
    for s2 in norm_str_list[1:]:
        [diffs_set.add(i) for i in range(max_length) if s1[i] != s2[i]]
    mismatch_start = min(diffs_set)
    mismatch_end = max(diffs_set)
    return [s[mismatch_start:mismatch_end+1].strip() for s in norm_str_list]

def _remove_number_padding(s):
    number_str = ''
    ret_str = ''
    for c in s:
        if c.isdigit():
            number_str += c
        else:
            if number_str:
                ret_str += '{}'.format(int(number_str))
                number_str = ''
            ret_str += c
    if number_str:
        ret_str += '{}'.format(int(number_str))
    return ret_str

@transaction.atomic
def _save_mapping(request):
    # Add stuff in Solr if POST arguments
    # A file dump should also be created so that Solr can be refreshed

    manuscript_id = request.POST['manuscript_id']
    manuscript = Manuscript.objects.get(id=manuscript_id)
    data = [['folio', 'uri']] # CSV column headers

    for index, value in request.POST.items():
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
