from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from neumeeditor.helpers.gamera_xml_importer import GameraXML
from neumeeditor.models import Glyph


class GameraXMLUploadView(APIView):
    parser_classes = (FileUploadParser,)
    renderer_classes = (JSONRenderer, JSONPRenderer)

    def put(self, request, filename, format=None):
        file_string = request.FILES['file'].read()



        return Response(status=204)
