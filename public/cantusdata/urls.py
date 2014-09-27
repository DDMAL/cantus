from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from cantusdata.views.manuscript import ManuscriptList, ManuscriptDetail
from cantusdata.views.chant import ChantList, ChantDetail
from cantusdata.views.folio import FolioList, FolioDetail
from cantusdata.views.concordance import ConcordanceList, ConcordanceDetail
from cantusdata.views.search import SearchView
from cantusdata.views.search_notation import SearchNotationView
from cantusdata.views.chant_set import FolioChantSetView, ManuscriptChantSetView
from cantusdata.views.folio_set import ManuscriptFolioSetView


urlpatterns = []

urlpatterns += format_suffix_patterns(
    patterns('cantusdata.views.main',
             url(r'^$', 'home'),
             url(r'^browse/$', 'api_root'),
             #url(r'^/$', ManuscriptList.as_view(), name="manuscript-list"),
             # Manuscripts
             url(r'^manuscripts/$', ManuscriptList.as_view(), name="manuscript-list"),
             url(r'^manuscript/(?P<pk>[0-9]+)/$', ManuscriptDetail.as_view(),
                 name="manuscript-detail"),
             # Folios
             url(r'^folios/$', FolioList.as_view(), name="folio-list"),
             url(r'^folio/(?P<pk>[0-9]+)/$', FolioDetail.as_view(),
                 name="folio-detail"),
             # Chants
             url(r'^chants/$', ChantList.as_view(), name="chant-list"),
             url(r'^chant/(?P<pk>[0-9]+)/$', ChantDetail.as_view(), name="chant-detail"),
             # Concordances
             url(r'^concordances/$', ConcordanceList.as_view(), name="concordance-list"),
             url(r'^concordance/(?P<pk>[0-9]+)/$', ConcordanceDetail.as_view(),
                 name="concordance-detail"),

             #######################
             # Direct Solr queries #
             #######################

             # Query chants by folio
             url(r'^chant-set/folio/(?P<pk>[0-9]+)/$',
                 FolioChantSetView.as_view(), name="folio-chant-set-view"),
             # Query chants by manuscript
             url(r'^chant-set/manuscript/(?P<pk>[0-9]+)/$',
                 ManuscriptChantSetView.as_view(),
                 name="manuscript-chant-set-view"),
             url(r'^chant-set/manuscript/(?P<pk>[0-9]+)/page-(?P<start>[0-9]+)/$',
                 ManuscriptChantSetView.as_view(),
                 name="manuscript-chant-set-view-page"),
             # Query Folios by manuscript
             url(r'^folio-set/manuscript/(?P<pk>[0-9]+)/$',
                 ManuscriptFolioSetView.as_view(),
                 name="manuscript-folio-set-view"),
             url(r'^folio-set/manuscript/(?P<pk>[0-9]+)/(?P<number>[a-zA-Z0-9]+)/$',
                 ManuscriptFolioSetView.as_view(),
                 name="manuscript-folio-set-view-index"),
             # Search
             url(r'^search/$', SearchView.as_view(), name="search-view"),
             url(r'^admin/', include(admin.site.urls)),

             # Notation search
             url(r'^notation-search/$', SearchNotationView.as_view(),
                 name="search-notation-view"),
             )
)
