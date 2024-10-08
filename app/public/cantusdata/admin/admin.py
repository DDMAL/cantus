from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models import Model
from django.db.models.query import QuerySet
from django.http import HttpRequest

from django_celery_results.models import TaskResult  # type: ignore[import-untyped]
from django_celery_results.admin import TaskResultAdmin  # type: ignore[import-untyped]

from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio
from cantusdata.models.plugin import Plugin
from cantusdata.models.neume_exemplar import NeumeExemplar
from cantusdata.tasks import chant_import_task


@admin.action(description="ReIndex in Solr")
def reindex_in_solr(
    modeladmin: ModelAdmin,  # type: ignore[type-arg]
    request: HttpRequest,
    queryset: QuerySet[Model],
) -> None:
    for item in queryset:
        item.save()


class ManuscriptAdmin(ModelAdmin):  # type: ignore[type-arg]
    actions = [reindex_in_solr, "load_chants"]
    ordering = ["-public", "name"]
    list_per_page = 200
    change_form_template = "admin/manuscript_change_form.html"
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
        (
            "Status",
            {
                "fields": [
                    "public",
                    "chants_loaded",
                    "is_mapped",
                    "dbl_folio_img",
                ]
            },
        ),
        (
            "Search",
            {
                "fields": [
                    "plugins",
                ]
            },
        ),
    ]
    readonly_fields = (
        "folio_count",
        "chant_count",
        "siglum_slug",
        "chants_loaded",
        "is_mapped",
        "dbl_folio_img",
    )
    list_display = ("name", "siglum", "public", "chants_loaded", "is_mapped")

    @admin.action(
        description="Imports the chants associated \
        with the selected manuscript(s)"
    )
    def load_chants(self, request: HttpRequest, queryset: QuerySet[Manuscript]) -> None:
        for ms in queryset:
            chant_import_task.apply_async(kwargs={"manuscript_ids": [ms.pk]})
        self.message_user(
            request,
            (
                "Importing chants for the selected manuscripts. "
                "This may take a few minutes. "
                "Check status on the Task Results page."
            ),
        )


class ChantAdmin(ModelAdmin):  # type: ignore[type-arg]
    actions = [reindex_in_solr]


class FolioAdmin(ModelAdmin):  # type: ignore[type-arg]
    actions = [reindex_in_solr]
    readonly_fields = ("chant_count",)


class PluginAdmin(ModelAdmin):  # type: ignore[type-arg]
    readonly_fields = ("slug",)


class NeumeExemplarAdmin(ModelAdmin):  # type: ignore[type-arg]
    list_display = ("name", "folio")
    readonly_fields = ("admin_image",)


class NewTaskResultAdmin(TaskResultAdmin):  # type: ignore[misc]
    list_display = ("task_name", "date_done", "status", "get_task_manuscript_ids")
    list_filter = ("status", "date_done", "task_name")

    @admin.display(description="Manuscript(s)")
    def get_task_manuscript_ids(self, obj: TaskResult) -> list[Manuscript]:
        if obj.status == "RECEIVED":
            obj_man_ids = eval(obj.task_kwargs)["manuscript_ids"]
        else:
            obj_man_ids = eval(obj.task_kwargs[1:-1])["manuscript_ids"]
        if not isinstance(obj_man_ids, list):
            obj_man_ids = [obj_man_ids]
        task_manuscripts = [
            man for man in Manuscript.objects.filter(id__in=obj_man_ids)
        ]
        return task_manuscripts


admin.site.register(Manuscript, ManuscriptAdmin)
admin.site.register(Chant, ChantAdmin)
admin.site.register(Folio, FolioAdmin)
admin.site.register(Plugin, PluginAdmin)
admin.site.register(NeumeExemplar, NeumeExemplarAdmin)
admin.site.unregister(TaskResult)
admin.site.register(TaskResult, NewTaskResultAdmin)
