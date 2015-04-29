from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static
from neumeeditor.views.authentication import ObtainExpiringAuthToken
from neumeeditor.views.image import ImageList, ImageDetail
from neumeeditor.views.main import neumeeditor_home, neumeeditor_api_root
from neumeeditor.views.name import NameList, NameDetail
from neumeeditor.views.nomenclature import NomenclatureDetail, NomenclatureList
from neumeeditor.views.style import StyleList, StyleDetail
from neumeeditor.views.user import UserList, UserDetail
from rest_framework.urlpatterns import format_suffix_patterns
from neumeeditor.views.glyph import GlyphDetail, GlyphList


urlpatterns = []

urlpatterns += format_suffix_patterns(
    patterns('cantusdata.views.main',
             url(r'^$', neumeeditor_home),
             url(r'^browse/$', neumeeditor_api_root),

             url(r'^glyphs/$', GlyphList.as_view(), name="glyph-list"),
             url(r'^glyph/(?P<pk>[0-9]+)/$', GlyphDetail.as_view(),
                 name="glyph-detail"),

             url(r'^names/$', NameList.as_view(), name="name-list"),
             url(r'^name/(?P<pk>[0-9]+)/$', NameDetail.as_view(),
                 name="name-detail"),

             url(r'^images/$', ImageList.as_view(), name="image-list"),
             url(r'^image/(?P<pk>[0-9]+)/$', ImageDetail.as_view(),
                 name="image-detail"),

             url(r'^styles/$', StyleList.as_view(), name="style-list"),
             url(r'^style/(?P<pk>[0-9]+)/$', StyleDetail.as_view(),
                 name="style-detail"),

             # url(r'^users/$', UserList.as_view(), name="user-list"),
             # url(r'^user/(?P<pk>[0-9]+)/$', UserDetail.as_view(),
             #     name="user-detail"),

             url(r'^nomenclatures/$', NomenclatureList.as_view(),
                 name="nomenclature-list"),
             url(r'^nomenclature/(?P<pk>[0-9]+)/$',
                 NomenclatureDetail.as_view(), name="nomenclature-detail"),

             )
)

# Handle media
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Auth
urlpatterns += patterns('', url(r'^auth/', ObtainExpiringAuthToken.as_view()))
