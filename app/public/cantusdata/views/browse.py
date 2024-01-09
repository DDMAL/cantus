from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(("GET",))
def browse_view(request, format=None):
    return Response(
        {
            "manuscripts": reverse("manuscript-list", request=request, format=format),
            "chants": reverse("chant-list", request=request, format=format),
            "folios": reverse("folio-list", request=request, format=format),
        }
    )
