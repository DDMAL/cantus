from django.contrib import admin
from neumeeditor.models import Name
from neumeeditor.models.glyph import Glyph
from neumeeditor.models.image import Image
from neumeeditor.models.style import Style


class NameInline(admin.TabularInline):
    model = Name

class ImageInline(admin.TabularInline):
    model = Image


class GlyphAdmin(admin.ModelAdmin):
    inlines = [
        NameInline,
        ImageInline
    ]

class StyleAdmin(admin.ModelAdmin):
    pass


class NameAdmin(admin.ModelAdmin):
    pass


admin.site.register(Glyph, GlyphAdmin)
admin.site.register(Style, StyleAdmin)
admin.site.register(Name, NameAdmin)
