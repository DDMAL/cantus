from django.contrib import admin
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant
from cantusdata.models.concordance import Concordance
from cantusdata.models.folio import Folio
from cantusdata.models.plugin import Plugin
from cantusdata.models.neume_exemplar import NeumeExemplar
from cantusdata.tasks import chant_import_task
from django.core.management import call_command
from django.http import HttpResponseRedirect


def reindex_in_solr(modeladmin, request, queryset):
    for item in queryset:
        item.save()


reindex_in_solr.short_description = "ReIndex in Solr"


class ManuscriptAdmin(admin.ModelAdmin):
    actions = [reindex_in_solr, "load_chants"]
    list_per_page = 200
    fieldsets = [
        (
            "Metadata",
            {
                "fields": [
                    "name",
                    "siglum",
                    "siglum_slug",
                    "date",
                    "provenance",
                    "description",
                    "folio_count",
                    "chant_count",
                ]
            },
        ),
        (
            "Sources",
            {"fields": ["cantus_url", "csv_export_url", "manifest_url"]},
        ),
        ("Status", {"fields": ["public", "chants_loaded", "is_mapped"]}),
    ]
    readonly_fields = (
        "folio_count",
        "chant_count",
        "siglum_slug",
        "chants_loaded",
        "is_mapped",
    )
    list_display = ("name", "siglum", "public", "chants_loaded", "is_mapped")

    @admin.action(
        description="Imports the chants associated \
        with the selected manuscript(s)"
    )
    def load_chants(self, request, queryset):
        for ms in queryset:
            chant_import_task.apply_async(kwargs={"manuscript_ids": [ms.pk]})
        self.message_user(
            request,
            "Importing chants for the selected manuscripts. This may take a few minutes. Check status on the Task Results page.",
        )


class ChantAdmin(admin.ModelAdmin):
    actions = [reindex_in_solr]


class FolioAdmin(admin.ModelAdmin):
    actions = [reindex_in_solr]
    readonly_fields = ("chant_count",)


class ConcordanceAdmin(admin.ModelAdmin):
    actions = [reindex_in_solr]
    readonly_fields = ("citation",)


class PluginAdmin(admin.ModelAdmin):
    readonly_fields = ("slug",)


class NeumeExemplarAdmin(admin.ModelAdmin):
    list_display = ("admin_image", "__str__")
    readonly_fields = ("admin_image",)


admin.site.register(Manuscript, ManuscriptAdmin)
admin.site.register(Chant, ChantAdmin)
admin.site.register(Concordance, ConcordanceAdmin)
admin.site.register(Folio, FolioAdmin)
admin.site.register(Plugin, PluginAdmin)
admin.site.register(NeumeExemplar, NeumeExemplarAdmin)
