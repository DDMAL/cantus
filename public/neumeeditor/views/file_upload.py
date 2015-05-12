from lxml.etree import XMLSyntaxError
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from neumeeditor.helpers.gamera_xml_importer import import_gamera_data
from neumeeditor.helpers.mei_importer import import_mei_data


class GameraXMLUploadView(APIView):
    parser_classes = (FileUploadParser,)
    renderer_classes = (JSONRenderer, JSONPRenderer)

    def post(self, request, format=None):
        # Get a string of the file
        file_string = request.FILES['file'].read()
        # Extract the data
        try:
            import_gamera_data(file_string)
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
        try:
            import_mei_data(file_string, file_name)
        except XMLSyntaxError:
            return Response(data={"error": "Error parsing MEI."},
                            status=500)
        # Did it work?
        return Response(data={"success": "MEI file parsed successfully."},
                        status=201)
