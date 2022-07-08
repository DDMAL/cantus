from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from django.core.management import call_command
from django.db import transaction
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
from cantusdata.tasks import map_folio_task
import urllib.request, urllib.parse, urllib.error
import json
import csv
import re
import threading


class MapFoliosView(APIView):
    template_name = "admin/map_folios.html"
    renderer_classes = (TemplateHTMLRenderer,)

    def get(self, request, *args, **kwargs):
        # Return the URIs and folio names

        # If no manuscript specified,
        # display list of manuscripts and mapping status.
        if "manuscript_id" not in request.GET:
            manuscripts = Manuscript.objects.filter(
                manifest_url__isnull=False, public=True, chants_loaded=True
            )
            manuscript_ids = [(m.id, str(m), m.is_mapped) for m in manuscripts]

            return Response({"manuscript_ids": manuscript_ids})

        # If manuscript is specified, retrieve manuscript object
        # from db.
        manuscript_id = int(request.GET["manuscript_id"])
        manuscript_obj = Manuscript.objects.get(id=manuscript_id)
        manifest = manuscript_obj.manifest_url

        # Get IIIF manifest from manifest link.
        # Get individual URIs of manuscript.
        uris_objs = []
        uris = []
        manifest_json = urllib.request.urlopen(manifest)
        manifest_data = json.loads(manifest_json.read().decode("utf-8"))
        for canvas in manifest_data["sequences"][0]["canvases"]:
            service = canvas["images"][0]["resource"]["service"]
            uri = service["@id"]
            uris.append(uri)
            path_tail = (
                "default.jpg"
                if service["@context"] == "http://iiif.io/api/image/2/context.json"
                else "native.jpg"
            )
            uris_objs.append(
                {
                    "full": uri,
                    "thumbnail": uri + "/full/,160/0/" + path_tail,
                    "large": uri + "/full/,1800/0/" + path_tail,
                    "short": re.sub(r"^.*/(?!$)", "", uri),
                }
            )
        # Get unique ids in uri strings
        uri_ids = _extract_ids(uris)
        # Query db for folios associated with manuscript
        folios = []
        folio_imagelink = {}
        uri_folio_map = {}
        folios_query = Folio.objects.filter(manuscript__id=manuscript_id)
        man_is_mapped = manuscript_obj.is_mapped

        # Create list of folios.
        # Map folios to previously-linked image and/or uri.
        for folio in folios_query:
            folios.append(folio.number)
            if folio.image_link:
                folio_imagelink[folio.number] = folio.image_link
            if man_is_mapped == "MAPPED":
                uri_folio_map[folio.image_uri] = folio.number

        imagelinks = list(folio_imagelink.values())
        imagelinks_ids = _extract_ids(imagelinks)
        imagelink_folio = {k: v for k, v in zip(imagelinks_ids, folio_imagelink.keys())}

        mapped_folios = 0
        for idx, uri in enumerate(uris_objs):
            uri["id"] = uri_ids[idx]
            uri["folio"] = None
            if man_is_mapped == "MAPPED":
                uri["folio"] = uri_folio_map.get(uri["full"], "")
                mapped_folios += 1
            else:
                if uri["id"] in imagelink_folio:
                    uri["folio"] = imagelink_folio[uri["id"]]
                    mapped_folios += 1

        # If previously-linked uris do not exist,
        # or previously-linked images do not contain folio id's,
        # map images to folios naively (nth image to nth folio).
        if mapped_folios == 0 and len(uris_objs) >= len(folios):
            for idx, folio in enumerate(folios):
                uris_objs[idx]["folio"] = folio

        return Response(
            {
                "uris": uris_objs,
                "folios": folios,
                "manuscript_id": manuscript_id,
            }
        )

    def post(self, request):
        try:
            thread = threading.Thread(target=_save_mapping, args=(request,), kwargs={})
            thread.start()
        except Exception as e:
            return Response({"error": e})

        return Response({"posted": True})


def _extract_ids(str_list):
    if not str_list:
        return []
    # string a: $OME/EXAMPLE/CR4ZY/STRING/123anid!!SOMEMOREIDENTICALSTUFF
    # string b: $OME/EXAMPLE/CR4ZY/STRING/123anotherid!!SOMEMOREIDENTICALSTUFF
    left_sweep = _remove_longest_common_string(str_list, "left")
    # string a: anid!!SOMEMOREIDENTICALSTUFF
    # string b: anotherid!!SOMEMOREIDENTICALSTUFF
    right_sweep = _remove_longest_common_string(left_sweep, "right")
    # string a: anid
    # string b: anotherid
    ids = [_remove_number_padding(s) for s in right_sweep]
    return ids


def _remove_longest_common_string(str_list, align="left"):
    longest_str = max(str_list, key=len)
    max_length = len(longest_str)
    if align == "left":
        norm_str_list = [s.ljust(max_length) for s in str_list]
    elif align == "right":
        norm_str_list = [s.rjust(max_length) for s in str_list]
    s1 = norm_str_list[0]
    diffs_set = set()
    for s2 in norm_str_list[1:]:
        [diffs_set.add(i) for i in range(max_length) if s1[i] != s2[i]]
    mismatch_start = min(diffs_set)
    mismatch_end = max(diffs_set)
    return [s[mismatch_start : mismatch_end + 1].strip() for s in norm_str_list]


def _remove_number_padding(s):
    number_str = ""
    ret_str = ""
    for c in s:
        if c.isdigit():
            number_str += c
        else:
            if number_str:
                ret_str += f"{int(number_str)}"
                number_str = ""
            ret_str += c
    if number_str:
        ret_str += f"{int(number_str)}"
    return ret_str


@transaction.atomic
def _save_mapping(request):
    """Called in case of a POST request to map_folios.
    Contents of post request should have:
    - a csrfmiddlewaretoken key-value pair
    - a manuscript_id key with the id of mapped manuscript as value
    - a series of key-value pairs where key is a IIIF uri
      and values is a folio name
    Creates a temporary csv dump of folio mapping data and
    calls the import_folio_mapping command."""

    manuscript_id = request.POST["manuscript_id"]
    manuscript = Manuscript.objects.get(id=manuscript_id)
    manuscript.is_mapped = "PENDING"
    manuscript.save()

    # Create list of data for saving
    # with column headers "folio" and "uri"
    data = []
    for index, value in request.POST.items():
        # 'index' should be the uri, and 'value' the folio name
        if (
            index == "csrfmiddlewaretoken"
            or index == "manuscript_id"
            or len(value) == 0
        ):
            continue
        data.append({"folio": value, "uri": index})

    map_folio_task.apply_async(kwargs={"manuscript_id": manuscript_id, "data": data})
