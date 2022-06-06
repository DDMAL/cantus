from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from django.core.management import call_command
import threading


class LoadChantsView(APIView):
    template_name = "admin/load_chants.html"
    renderer_classes = (TemplateHTMLRenderer,)

    def get(self, request):
        manuscript_ids = request.GET["manuscript_ids"].split(",")
        try:
            for man_id in manuscript_ids:
                thread = threading.Thread(
                    target=call_command,
                    args=(
                        "import_data",
                        "chants",
                        f"--manuscript-id={man_id}",
                    ),
                    kwargs={},
                )
                thread.start()
        except Exception as e:
            return Response({"error": e})

        return Response({"manuscript_ids": manuscript_ids})
