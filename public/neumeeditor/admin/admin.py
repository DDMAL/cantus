from django.contrib import admin
from neumeeditor.models import Name
from neumeeditor.models.glyph import Glyph
from neumeeditor.models.style import Style


class NameInline(admin.TabularInline):
    model = Name


class GlyphAdmin(admin.ModelAdmin):
    inlines = [
        NameInline
    ]


class StyleAdmin(admin.ModelAdmin):
    pass


class NameAdmin(admin.ModelAdmin):
    pass


admin.site.register(Glyph, GlyphAdmin)
admin.site.register(Style, StyleAdmin)
admin.site.register(Name, NameAdmin)
