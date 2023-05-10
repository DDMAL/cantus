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
        """
        A GET request to the map folios page can have two different states:
        1. No manuscript_id is specified in the request. In this case, we display
        a list of manuscripts and their mapping status.
        2. A manuscript_id is specified in the request. In this case, the user
        has specified a manuscript to map (or re-map). In this case, we display
        the mapping tool.
        """
        # If no manuscript specified,
        # display list of manuscripts and mapping status.
        if "manuscript_id" not in request.GET:
            manuscripts = Manuscript.objects.filter(
                manifest_url__isnull=False, public=True, chants_loaded=True
            )
            manuscript_ids = [(m.id, str(m), m.is_mapped) for m in manuscripts]

            return Response({"manuscript_ids": manuscript_ids})

        # If manuscript is specified, retrieve manuscript object
        # and that manuscripts folios from db.
        manuscript_id = int(request.GET["manuscript_id"])
        manuscript_obj = Manuscript.objects.get(id=manuscript_id)
        folios_objs = Folio.objects.filter(manuscript__id=manuscript_id)
        folios = [f.number for f in folios_objs]
        map_status = manuscript_obj.is_mapped
        dbl_folio_img = manuscript_obj.dbl_folio_img
        manifest_url = manuscript_obj.manifest_url

        # Extract individual image uris and ids from the manifest.
        uris, uris_objs = _extract_uris_from_manifest(manifest_url)
        uri_ids = _extract_ids(uris)

        # If the manuscript has not yet been mapped in Cantus Ultimus,
        # we first check to see if a mapping between folios and images was
        # imported alongside chant data from CantusDB (these would be
        # stored in the "image_link" field of the folio object)
        if map_status == "UNMAPPED":
            imagelink_folio_map = _extract_imagelinks(folios_objs)

        # Iterate through all the image uris extracted from the manifest.
        # When a manuscript is already mapped,
        # map uris to folios based on the existing image_uri field.
        # Where not mapped, try to map uris to folios based on the
        # image_link field. If a manuscript is not mapped, and
        # the image_link field is empty or yields no mapping,
        # map uris to folios naively (first uri to first folio, etc.)
        any_previously_mapped_folios = False
        for idx, uri in enumerate(uris_objs):
            uri["id"] = uri_ids[idx]
            uri["folio"] = None
            if map_status == "MAPPED":
                fols_w_uri = folios_objs.filter(image_uri=uri["full"])
                uri["folio"] = [f.number for f in fols_w_uri]
                any_previously_mapped_folios = True
            else:
                if uri["id"] in imagelink_folio_map:
                    uri["folio"] = [imagelink_folio_map[uri["id"]]]
                    any_previously_mapped_folios = True

        if not any_previously_mapped_folios and len(uris_objs) >= len(folios):
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


def _extract_uris_from_manifest(manifest_url):
    """
    Downloads the IIIF manifest from the provided url and extracts
    the uris for individual images in the manuscript.
    Returns a list of these uris, as well as a list of dictionaries
    containing the image uri (key: "full") as well as constructed
    requests to thumbnail (key: "thumbnail") and large (key: "large") versions
    of the image for use on the folio mapping page.
    """
    uris_objs = []
    uris = []
    manifest_json = urllib.request.urlopen(manifest_url)
    manifest_data = json.loads(manifest_json.read().decode("utf-8"))
    for canvas in manifest_data["sequences"][0]["canvases"]:
        service = canvas["images"][0]["resource"]["service"]
        uri = service["@id"]
        uris.append(uri)
        path_tail = "default.jpg"
        uris_objs.append(
            {
                "full": uri,
                "thumbnail": uri + "/full/,160/0/" + path_tail,
                "large": uri + "/full/,1800/0/" + path_tail,
            }
        )
    return uris, uris_objs


def _extract_imagelinks(folios_objs):
    """
    Extracts image links, if available, from the folios queryset.

    Parameters
    ----------
    folios_objs : django.db.models.query.QuerySet
        Queryset of Folio objects.
    """
    imagelinks_folios = folios_objs.values_list("number", "image_link")
    imagelinks_ids = _extract_ids([i[1] for i in imagelinks_folios if len(i[1]) > 0])
    imagelink_folio_map = dict(zip(imagelinks_ids, [i[0] for i in imagelinks_folios]))
    return imagelink_folio_map


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
