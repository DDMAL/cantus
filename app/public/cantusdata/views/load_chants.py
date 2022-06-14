from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from celery.result import AsyncResult

class LoadChantsView(APIView):
    template_name = "admin/load_chants.html"
    renderer_classes = (TemplateHTMLRenderer,)

    def get(self, request):
        task_id = request.GET["id"]
        result = AsyncResult(task_id)
        response_ = result.info
        return Response({"num_processed": response_, "task_id":task_id})