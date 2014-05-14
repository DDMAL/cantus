from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(('GET',))
def api_root(request, format=None):
    return Response({'manuscripts': reverse('manuscript-list', request=request, format=format),
                     'chants': reverse('chant-list', request=request, format=format)})

@ensure_csrf_cookie
def home(request):
    data = {}
    #return render(request, "index.html", data)
    return render(request, "manuscript/manuscript_list.html", data)