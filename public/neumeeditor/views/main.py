from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(('GET',))
def neumeeditor_api_root(request, format=None):
    return Response({'glyphs': reverse('glyph-list', request=request,
                                            format=format),
                     'styles': reverse('style-list', request=request,
                                       format=format)})


@ensure_csrf_cookie
def neumeeditor_home(request):
    data = {}
    return render(request, "neumeeditor/index.html", data)
