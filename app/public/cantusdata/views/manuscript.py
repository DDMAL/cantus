from rest_framework import generics
from cantusdata.models.manuscript import Manuscript
from cantusdata.serializers.manuscript import (
    ManuscriptSerializer,
    ManuscriptListSerializer,
)
from cantusdata.renderers import templated_view_renderers
from django.http import Http404, HttpResponseNotFound
from django.shortcuts import render
from rest_framework.response import Response
from cantusdata.metrics.definitions import MANUSCRIPT_VIEWS
from cantusdata.metrics.labels import classify_client, manuscript_label


class ManuscriptList(generics.ListAPIView):
    model = Manuscript
    queryset = Manuscript.objects.filter(public=True)
    serializer_class = ManuscriptListSerializer
    template_name = "require.html"
    renderer_classes = templated_view_renderers


class ManuscriptDetail(generics.RetrieveAPIView):
    model = Manuscript
    queryset = Manuscript.objects.filter(public=True)
    serializer_class = ManuscriptSerializer
    template_name = "require.html"
    renderer_classes = templated_view_renderers

    def retrieve(self, request, *args, **kwargs):
        """
        Overrides the default retrieval method
        to return a custom 404 page if the manuscript
        is not found. Implemented to prevent generic
        404 errors from links to specific manuscripts
        made before manuscript ids were stable.
        """

        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            # The HTML route only serves the app shell, which then fetches this
            # same URL as JSON: counting the JSON fetch counts each open once.
            if request.accepted_renderer.format == "json":
                MANUSCRIPT_VIEWS.labels(
                    manuscript_label(instance.pk), classify_client(request)
                ).inc()
            return Response(serializer.data)
        except Http404:
            return HttpResponseNotFound(
                render(request, "missing_manuscript_redirect.html")
            )
