from lxml.etree import XMLSyntaxError
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from neumeeditor.helpers.gamera_xml_importer import GameraXML
from neumeeditor.helpers.gamera_xml_importer import import_gamera_data


class GameraXMLUploadView(APIView):
    parser_classes = (FileUploadParser,)
    renderer_classes = (JSONRenderer, JSONPRenderer)

    def post(self, request, format=None):
        for key, value in request.FILES.iteritems():
            print (key, value)
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



        return Response(status=204)
