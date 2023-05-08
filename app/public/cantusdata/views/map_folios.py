from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
from cantusdata.tasks import map_folio_task
from django.http import HttpResponseRedirect
import re
import json
import urllib.request
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
        folios_query = Folio.objects.filter(manuscript__id=manuscript_id)
        folios = [f.number for f in folios_query]
        map_status = manuscript_obj.is_mapped
        dbl_folio_img = manuscript_obj.dbl_folio_img

        # Create a dictionary mapping IDs extracted
        # from the image_link field (where it exists)
        # to folio numbers.
        if map_status == "UNMAPPED":
            imagelinks = folios_query.values_list("number", "image_link")
            imagelinks_ids = _extract_ids([i[1] for i in imagelinks if len(i[1]) > 0])
            imagelink_folio = {
                k: v for k, v in zip(imagelinks_ids, [i[0] for i in imagelinks])
            }

        # Iterate through manifest uris.
        # When a manuscript is already mapped,
        # map uris to folios based on the existing image_uri field.
        # Where not mapped, try to map uris to folios based on the
        # image_link field. If a manuscript is not mapped, and
        # no image_link field exists, map uris to folios naively (first
        # uri to first folio, etc.)
        mapped_folios = 0
        for idx, uri in enumerate(uris_objs):
            uri["id"] = uri_ids[idx]
            uri["folio"] = None
            if map_status == "MAPPED":
                fols_w_uri = folios_query.filter(image_uri=uri["full"])
                uri["folio"] = [f.number for f in fols_w_uri]
                mapped_folios += 1
            else:
                if uri["id"] in imagelink_folio:
                    uri["folio"] = [imagelink_folio[uri["id"]]]
                    mapped_folios += 1

        if mapped_folios == 0 and len(uris_objs) >= len(folios):
            for idx, folio in enumerate(folios):
                uris_objs[idx]["folio"] = [folio]

        return Response(
            {
                "uris": uris_objs,
                "folios": folios,
                "manuscript_id": manuscript_id,
                "manuscript_mapping_state": map_status,
                "dbl_folio_img": dbl_folio_img,
            }
        )

    def post(self, request):
        try:
            thread = threading.Thread(target=_save_mapping, args=(request,), kwargs={})
            thread.start()
        except Exception as e:
            return Response({"error": e})

        return HttpResponseRedirect("/admin/map_folios/")


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


def _save_mapping(request):
    """Called in case of a POST request to map_folios.
    Contents of post request should have:
    - a csrfmiddlewaretoken key-value pair
    - a two_folio_images key with "on" or "off" result
    - a manuscript_id key with the id of mapped manuscript as value
    - a series of key-value pairs where key is a IIIF uri
      and values is a folio name
    Calls the import_folio_mapping command."""
    # Set manuscript mapping status to pending
    # Record whether mapping involves images with
    # two folios.
    manuscript_id = request.POST["manuscript_id"]
    manuscript = Manuscript.objects.get(id=manuscript_id)
    dbl_folio_img = True if request.POST.get("two_folio_images", None) else False
    manuscript.is_mapped = "PENDING"
    manuscript.dbl_folio_img = dbl_folio_img
    manuscript.save()

    # Create list of data for saving
    # with column headers "folio" and "uri"
    data = []
    for index, value in request.POST.lists():
        # 'index' should be the uri, and 'value' the folio name
        if (
            index == "csrfmiddlewaretoken"
            or index == "manuscript_id"
            or index == "two_folio_images"
        ):
            continue
        for fol in value:
            if len(fol) == 0:
                continue
            data.append({"folio": fol, "uri": index})

    map_folio_task.apply_async(kwargs={"manuscript_ids": manuscript_id, "data": data})
