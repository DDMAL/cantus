from django.conf.urls import patterns, include, url
from django.contrib import admin

from rest_framework.urlpatterns import format_suffix_patterns

from cantusdata.views.manuscript import ManuscriptList, ManuscriptDetail
from cantusdata.views.chant import ChantList, ChantDetail
from cantusdata.views.search import SearchView


urlpatterns = []

urlpatterns += format_suffix_patterns(
    patterns('cantusdata.views.main',
    url(r'^$', 'home'),
    url(r'^browse/$', 'api_root'),
    #url(r'^/$', ManuscriptList.as_view(), name="manuscript-list"),
    url(r'^manuscripts/$', ManuscriptList.as_view(), name="manuscript-list"),
    url(r'^manuscript/(?P<pk>[0-9]+)/$', ManuscriptDetail.as_view(), name="manuscript-detail"),
    url(r'^chants/$', ChantList.as_view(), name="chant-list"),
    url(r'^chant/(?P<pk>[0-9]+)/$', ChantDetail.as_view(), name="chant-detail"),
    url(r'^search/$', SearchView.as_view(), name="search-view"),

    url(r'^admin/', include(admin.site.urls)),
))