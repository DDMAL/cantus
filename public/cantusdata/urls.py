# from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from cantusdata.views.browse import browse_view
from cantusdata.views.manuscript import ManuscriptList, ManuscriptDetail
from cantusdata.views.chant import ChantList, ChantDetail
from cantusdata.views.folio import FolioList, FolioDetail
from cantusdata.views.concordance import ConcordanceList, ConcordanceDetail
from cantusdata.views.search import SearchView
from cantusdata.views.suggestion import SuggestionView
from cantusdata.views.search_notation import SearchNotationView
from cantusdata.views.chant_set import (
    FolioChantSetView,
    ManuscriptChantSetView,
)
from cantusdata.views.folio_set import ManuscriptFolioSetView
from cantusdata.views.manuscript_glyph_set import ManuscriptGlyphSetView
from cantusdata.views.map_folios import MapFoliosView
from cantusdata.views.manifest_proxy import ManifestProxyView
from cantusdata.views import staticpages
from django.contrib.admin.views.decorators import staff_member_required

from django.urls import path, re_path, include

urlpatterns = [
    # Admin pages
    path("admin/", admin.site.urls),
    path(
        "admin/map_folios/",
        staff_member_required(MapFoliosView.as_view()),
        name="map-folios-view",
    ),
    # Static pages
    path("", staticpages.homepage, name="homepage"),
    path("about/", staticpages.about, name="about"),
    path("team/", staticpages.team, name="team"),
    path("activities/", staticpages.activities, name="activities"),
    path("browse/", browse_view, name="api-root"),
    # Main pages
    path("manuscripts/", ManuscriptList.as_view(), name="manuscript-list"),
    path(
        "manuscript/<int:pk>/",
        ManuscriptDetail.as_view(),
        name="manuscript-detail",
    ),
    path("folios/", FolioList.as_view(), name="folio-list"),
    path("folio/<int:pk>/", FolioDetail.as_view(), name="folio-detail"),
    path("chants/", ChantList.as_view(), name="chant-list"),
    path("chant/<int:pk>/", ChantDetail.as_view(), name="chant-detail"),
    path("concordances/", ConcordanceList.as_view(), name="concordance-list"),
    path(
        "concordance/<int:pk>/",
        ConcordanceDetail.as_view(),
        name="concordance-detail",
    ),
    #######################
    # Direct Solr queries #
    #######################
    # Query chants by folio
    path(
        "chant-set/folio/<int:pk>/",
        FolioChantSetView.as_view(),
        name="folio-chant-set-view",
    ),
    # Query chants by manuscript
    path(
        "chant-set/manuscript/<int:pk>/",
        ManuscriptChantSetView.as_view(),
        name="manuscript-chant-set-view",
    ),
    path(
        "chant-set/manuscript/<int:pk>/page-<int:start>/",
        ManuscriptChantSetView.as_view(),
        name="manuscript-chant-set-view-page",
    ),
    path(
        "manuscript/<int:pk>/glyph-set",
        ManuscriptGlyphSetView.as_view(),
        name="manuscript-glyph-set-view-page",
    ),
    # Query folios by manuscript
    path(
        "folio-set/manuscript/<int:pk>/",
        ManuscriptFolioSetView.as_view(),
        name="manuscript-folio-set-view",
    ),
    path(
        "folio-set/manuscript/<int:pk>/<path:image_uri>/",
        ManuscriptFolioSetView.as_view(),
        name="manuscript-folio-set-view-index",
    ),
    # Search
    path("search/", SearchView.as_view(), name="search-view"),
    path("suggest/", SuggestionView.as_view(), name="suggestion-view"),
    # Work around Mixed Content errors in third-party manifest files
    path(
        "manifest-proxy/<path:manifest_url>/",
        ManifestProxyView.as_view(),
        name="retrieve-manifest",
    ),
    # Notation search
    path(
        "notation-search/",
        SearchNotationView.as_view(),
        name="search-notation-view",
    ),
]

# Disambiguates json/html/browsable-api urls
urlpatterns = format_suffix_patterns(urlpatterns)


# urlpatterns = format_suffix_patterns(
#     [
#         # Static Pages
#         url(r"^$", staticpages.homepage, name="homepage"),
#         url(
#             r"^(?P<static_page>about|team|activities)/$",
#             staticpages.general,
#             name="staticpage",
#         ),
#         # API Root
#         url(r"^browse/$", browse_view, name="api-root"),
#         # Manuscripts
#         url(
#             r"^manuscripts/$", ManuscriptList.as_view(), name="manuscript-list"
#         ),
#         url(
#             r"^manuscript/(?P<pk>[0-9]+)/$",
#             ManuscriptDetail.as_view(),
#             name="manuscript-detail",
#         ),
#         # Folios
#         url(r"^folios/$", FolioList.as_view(), name="folio-list"),
#         url(
#             r"^folio/(?P<pk>[0-9]+)/$",
#             FolioDetail.as_view(),
#             name="folio-detail",
#         ),
#         # Chants
#         url(r"^chants/$", ChantList.as_view(), name="chant-list"),
#         url(
#             r"^chant/(?P<pk>[0-9]+)/$",
#             ChantDetail.as_view(),
#             name="chant-detail",
#         ),
#         # Concordances
#         url(
#             r"^concordances/$",
#             ConcordanceList.as_view(),
#             name="concordance-list",
#         ),
#         url(
#             r"^concordance/(?P<pk>[0-9]+)/$",
#             ConcordanceDetail.as_view(),
#             name="concordance-detail",
#         ),
#         #######################
#         # Direct Solr queries #
#         #######################
#         # Query chants by folio
#         url(
#             r"^chant-set/folio/(?P<pk>[0-9]+)/$",
#             FolioChantSetView.as_view(),
#             name="folio-chant-set-view",
#         ),
#         # Query chants by manuscript
#         url(
#             r"^chant-set/manuscript/(?P<pk>[0-9]+)/$",
#             ManuscriptChantSetView.as_view(),
#             name="manuscript-chant-set-view",
#         ),
#         url(
#             r"^chant-set/manuscript/(?P<pk>[0-9]+)/page-(?P<start>[0-9]+)/$",
#             ManuscriptChantSetView.as_view(),
#             name="manuscript-chant-set-view-page",
#         ),
#         url(
#             r"^manuscript/(?P<pk>[0-9]+)/glyph-set$",
#             ManuscriptGlyphSetView.as_view(),
#             name="manuscript-glyph-set-view-page",
#         ),
#         # Query Folios by manuscript
#         url(
#             r"^folio-set/manuscript/(?P<pk>[0-9]+)/$",
#             ManuscriptFolioSetView.as_view(),
#             name="manuscript-folio-set-view",
#         ),
#         url(
#             r"^folio-set/manuscript/(?P<pk>[0-9]+)/(?P<image_uri>([!#$&-;=?-[\]_a-zA-Z0-9~]|%[0-9a-fA-F]{2})+)/$",
#             ManuscriptFolioSetView.as_view(),
#             name="manuscript-folio-set-view-index",
#         ),
#         # Search
#         url(r"^search/$", SearchView.as_view(), name="search-view"),
#         url(r"^suggest/$", SuggestionView.as_view(), name="suggestion-view"),
#         # Work around Mixed Content errors when loading manifests from other libraries
#         url(
#             r"^manifest-proxy/(?P<manifest_url>([!#$&-;=?-[\]_a-zA-Z0-9~]|%[0-9a-fA-F]{2})+)/$",
#             ManifestProxyView.as_view(),
#             name="retrieve-manifest",
#         ),
#         # Admin pages
#         url(
#             r"^admin/map_folios/",
#             staff_member_required(MapFoliosView.as_view()),
#             name="map-folios-view",
#         ),
#         url(r"^admin/", include(admin.site.urls)),
#         # Notation search
#         url(
#             r"^notation-search/$",
#             SearchNotationView.as_view(),
#             name="search-notation-view",
#         ),
#     ]
# )
