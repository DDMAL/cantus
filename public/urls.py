from django.conf.urls import include, url

urlpatterns = [
    url(r'^view/', include('cantusdata.urls')),
    url(r'^neumeeditor/', include('neumeeditor.urls')),
    url(r'^', include('django.contrib.flatpages.urls'))
]
