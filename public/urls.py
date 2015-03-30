from django.conf.urls import include, url

urlpatterns = [
    url(r'^', include('cantusdata.urls')),
    url(r'^glypheditor/', include('neumeeditor.urls')),
]
