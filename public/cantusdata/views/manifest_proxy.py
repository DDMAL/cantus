from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from django.http import Http404, HttpResponse
import urllib2
import json


class ManifestProxyView(APIView):
    """
    This View does the simple task of retrieving a IIIF manifest
    from a url and returning it as it is. The reason why the
    manifest is not directly fetched from the source is that this
    method avoids cross domain mixed content errors. A lot of the
    digital libraries don't support https and browsers thus block
    the retrieval of JSON files from them, if serving from https.
    """

    renderer_classes = (JSONRenderer, )

    def get(self, request, *args, **kwargs):

        manifest_url = kwargs['manifest_url']

        try:
            manifest_json = json.load(urllib2.urlopen(manifest_url))
        except urllib2.URLError:
            raise Http404("Could not retrieve manifest from given url")
        except ValueError: # Error while parsing the json
            return HttpResponse("Invalid JSON file", status=500)

        return Response(manifest_json)
