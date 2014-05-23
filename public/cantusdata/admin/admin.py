from django.contrib import admin
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant
from cantusdata.models.concordance import Concordance
from cantusdata.models.folio import Folio


def reindex_in_solr(modeladmin, request, queryset):
    for item in queryset:
        item.save()

reindex_in_solr.short_description = "ReIndex in Solr"


class ManuscriptAdmin(admin.ModelAdmin):
    actions = [reindex_in_solr]
    readonly_fields = ('folio_count', 'chant_count', 'siglum_slug')


class ChantAdmin(admin.ModelAdmin):
    actions = [reindex_in_solr]


class FolioAdmin(admin.ModelAdmin):
    actions = [reindex_in_solr]
    readonly_fields = ('chant_count',)


class ConcordanceAdmin(admin.ModelAdmin):
    actions = [reindex_in_solr]
    readonly_fields = ('citation',)

admin.site.register(Manuscript, ManuscriptAdmin)
admin.site.register(Chant, ChantAdmin)
admin.site.register(Concordance, ConcordanceAdmin)
admin.site.register(Folio, FolioAdmin)
