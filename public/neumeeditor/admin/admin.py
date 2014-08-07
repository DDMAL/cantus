from django.contrib import admin
from neumeeditor.models import Name
from neumeeditor.models.glyph import Glyph
from neumeeditor.models.neume_style import NeumeStyle


class NameInline(admin.TabularInline):
    model = Name


class GlyphAdmin(admin.ModelAdmin):
    inlines = [
        NameInline
    ]


class NeumeStyleAdmin(admin.ModelAdmin):
    pass


# class NameAdmin(admin.ModelAdmin):
#     pass


admin.site.register(Glyph, GlyphAdmin)
admin.site.register(NeumeStyle, NeumeStyleAdmin)
# admin.site.register(Name, NameAdmin)
