from django.contrib import admin
from neumeeditor.models import Name
from neumeeditor.models.glyph import Glyph
from neumeeditor.models.image import Image
from neumeeditor.models.name_nomenclature_membership import \
    NameNomenclatureMembership
from neumeeditor.models.style import Style
from neumeeditor.models.nomenclature import Nomenclature


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


class NomenclatureAdmin(admin.ModelAdmin):
    pass


class NameNomenclatureMembershipAdmin(admin.ModelAdmin):
    pass


admin.site.register(Glyph, GlyphAdmin)
admin.site.register(Style, StyleAdmin)
admin.site.register(Name, NameAdmin)
admin.site.register(Nomenclature, NomenclatureAdmin)
admin.site.register(NameNomenclatureMembership, NameNomenclatureMembershipAdmin)
