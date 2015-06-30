from lxml.etree import XMLSyntaxError
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from neumeeditor.helpers.importers.gamera_xml_importer import GameraXMLImporter
from neumeeditor.helpers.importers.mei_importer import MeiImporter


class GameraXMLUploadView(APIView):
    parser_classes = (FileUploadParser,)
    renderer_classes = (JSONRenderer, JSONPRenderer)

    def post(self, request, format=None):
        # Get a string of the file
        file_string = request.FILES['file'].read()
        file_name = request.FILES['file'].name
        # Extract the data
        importer = GameraXMLImporter(file_string, file_name)
        try:
            importer.import_data()
        except XMLSyntaxError:
            return Response(data={"error": "Error parsing GameraXML."},
                            status=500)
        # Did it work?
        return Response(data={"success": "GameraXML file parsed successfully."},
                        status=201)


class MEIUploadView(APIView):
    parser_classes = (FileUploadParser,)
    renderer_classes = (JSONRenderer, JSONPRenderer)

    def post(self, request, format=None):
        # Get a string of the file
        file_string = request.FILES['file'].read()
        file_name = request.FILES['file'].name.split(".mei")[0]
        # Extract the data
        importer = MeiImporter(file_string, file_name)
        try:
            importer.import_data()
        except XMLSyntaxError:
            return Response(data={"error": "Error parsing MEI."},
                            status=500)
        # Did it work?
        return Response(data={"success": "MEI file parsed successfully."},
                        status=201)
