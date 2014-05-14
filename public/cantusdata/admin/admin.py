from django.contrib import admin

from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant

def reindex_in_solr(modeladmin, request, queryset):
    for item in queryset:
        item.save()

reindex_in_solr.short_description = "ReIndex in Solr"

class ManuscriptAdmin(admin.ModelAdmin):
    actions = [reindex_in_solr]


class ChantAdmin(admin.ModelAdmin):
    actions = [reindex_in_solr]

admin.site.register(Manuscript, ManuscriptAdmin)
admin.site.register(Chant, ChantAdmin)
