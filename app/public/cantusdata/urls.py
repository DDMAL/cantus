# from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.urls import path
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
from cantusdata.views.load_chants import LoadChantsView
from cantusdata.views.manifest_proxy import ManifestProxyView
from cantusdata.views import staticpages
from django.contrib.admin.views.decorators import staff_member_required

urlpatterns = [
    # Admin pages
    # All custom admin pages should be added above the root
    # admin path. Root admin path is a catch-all.
    path(
        "admin/map_folios/",
        staff_member_required(MapFoliosView.as_view()),
        name="map-folios-view",
    ),
    path(
        "admin/cantusdata/manuscript/load_chants/",
        staff_member_required(LoadChantsView.as_view()),
        name="load-chants-view",
    ),
    path("admin/", admin.site.urls),
    # Static pages
    path("", staticpages.homepage, name="homepage"),
    path("about/", staticpages.about, name="about"),
    path("team/", staticpages.team, name="team"),
    path("activities/", staticpages.activities, name="activities"),
    path("manifests/", staticpages.manifests, name="manifests"),
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
        "chant-set/folio/<str:pk>/",
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


admin.site.site_header = "Cantus Ultimus Admin"
