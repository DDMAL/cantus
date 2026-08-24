from typing import Any

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Model
from django.db.models.query import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django_celery_results.admin import TaskResultAdmin  # type: ignore[import-untyped]
from django_celery_results.models import TaskResult  # type: ignore[import-untyped]

from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.mei_submission import (
    MEISubmission,
    OUTCOMES_REQUIRING_NOTE,
    REVIEW_OUTCOMES,
    SubmissionStatus,
)
from cantusdata.models.neume_exemplar import NeumeExemplar
from cantusdata.models.plugin import Plugin
from cantusdata.tasks import chant_import_task, publish_mei_submission_task


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
                    "id",
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

    def get_readonly_fields(
        self, request: HttpRequest, obj: Manuscript | None = None
    ) -> tuple[str, ...]:
        if obj:
            return self.readonly_fields + ("id",)
        return self.readonly_fields

    @admin.action(description="Imports the chants associated \
        with the selected manuscript(s)")
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


class MEISubmissionReviewForm(ModelForm):  # type: ignore[type-arg]
    """
    Validates a review decision, so an illegal one is a form error the reviewer
    can see and correct rather than a server error.
    """

    class Meta:
        model = MEISubmission
        fields = ["status", "review_note"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.initial_status = self.instance.status
        if "status" in self.fields:
            # Only the outcomes a reviewer may choose, plus wherever the
            # submission already stands (so saving other fields is possible).
            allowed = {self.initial_status} | {o.value for o in REVIEW_OUTCOMES}
            self.fields["status"].choices = [  # type: ignore[attr-defined]
                (value, label)
                for value, label in SubmissionStatus.choices
                if value in allowed
            ]

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        status = cleaned.get("status")
        if status is None or status == self.initial_status:
            return cleaned
        if not self.instance.can_transition_to(status):
            raise ValidationError(
                {
                    "status": (
                        "A submission is reviewed once, out of pending. This one is "
                        f"already {self.instance.get_status_display().lower()}."
                    )
                }
            )
        if (
            status in OUTCOMES_REQUIRING_NOTE
            and not (cleaned.get("review_note") or "").strip()
        ):
            raise ValidationError(
                {
                    "review_note": (
                        "Say why: this is the only thing the submitter will see "
                        "explaining the decision."
                    )
                }
            )
        return cleaned


class MEISubmissionAdmin(ModelAdmin):  # type: ignore[type-arg]
    """
    The review queue for MEI submitted by an external OMR pipeline.

    Publishing needs no explanation, so it is a bulk action. Requesting a
    correction or refusing a submission both have to tell the submitter why, so
    they go through the change form where there is a field to say it in.
    """

    actions = ["publish_submissions"]
    form = MEISubmissionReviewForm
    list_display = (
        "manuscript",
        "folio_number",
        "submitter",
        "status",
        "submitted_at",
        "mei_download",
    )
    # "manuscript" is displayed for every row, and mei_summary reaches through it
    # for the siglum; without this each row costs its own query for it.
    list_select_related = ("manuscript",)
    list_filter = ("status", "manuscript")
    search_fields = ("submitter", "folio_number")
    date_hierarchy = "submitted_at"
    fieldsets = [
        (
            "Submission",
            {
                "fields": [
                    "manuscript",
                    "folio",
                    "folio_number",
                    "submitter",
                    "comment",
                    "submitted_at",
                    "mei_summary",
                ]
            },
        ),
        (
            "Review",
            {
                "fields": [
                    "status",
                    "review_note",
                    "reviewed_by",
                    "reviewed_at",
                    "published_path",
                ]
            },
        ),
    ]
    readonly_fields = (
        "manuscript",
        "folio",
        "folio_number",
        "submitter",
        "comment",
        "submitted_at",
        "mei_summary",
        "reviewed_by",
        "reviewed_at",
        "published_path",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Submissions arrive over the API, from a real OMR run. There is nothing
        # sensible to hand-enter here.
        return False

    def get_readonly_fields(
        self, request: HttpRequest, obj: MEISubmission | None = None
    ) -> tuple[str, ...]:
        # The stored status, not obj.status: when a POST fails validation the
        # admin has already copied the submitted values onto the instance, so
        # reading obj.status here would make the fields readonly on redisplay
        # and hide the error the reviewer needs to see.
        stored_status = (
            MEISubmission.objects.filter(pk=obj.pk)
            .values_list("status", flat=True)
            .first()
            if obj is not None and obj.pk
            else None
        )
        if stored_status is not None and stored_status != SubmissionStatus.PENDING:
            # Already reviewed: the record stands as history.
            return self.readonly_fields + ("status", "review_note")
        return self.readonly_fields

    @admin.display(description="MEI")
    def mei_summary(self, obj: MEISubmission) -> str:
        """Size and a download link, rather than 120 KB of XML in a textarea."""
        if not obj.pk:
            return ""
        # The size is formatted before it reaches format_html: format_html
        # escapes each argument into a string first, so a "{:.1f}" placeholder
        # raises ValueError -- which the admin catches, rendering the whole
        # field as "-" and silently swallowing the download link.
        size_kb = f"{len(obj.mei.encode('utf-8')) / 1024:.1f}"
        return format_html(
            '{} KB &mdash; <a href="{}" download>download {}</a>',
            size_kb,
            reverse("admin:cantusdata_meisubmission_mei", args=[obj.pk]),
            obj.mei_filename,
        )

    @admin.display(description="MEI")
    def mei_download(self, obj: MEISubmission) -> str:
        """
        The same download, offered from the queue: a reviewer working through a
        batch can collect the files without opening each submission first.

        Deliberately barer than mei_summary -- no size, no filename -- because a
        changelist row already names the manuscript and folio, and the size is
        not what anyone is scanning the column for.
        """
        return format_html(
            '<a href="{}" download>download</a>',
            reverse("admin:cantusdata_meisubmission_mei", args=[obj.pk]),
        )

    def get_urls(self) -> list[Any]:
        from django.urls import path

        return [
            path(
                "<int:pk>/mei/",
                self.admin_site.admin_view(self.download_mei),
                name="cantusdata_meisubmission_mei",
            )
        ] + super().get_urls()

    def download_mei(self, request: HttpRequest, pk: int) -> HttpResponse:
        """
        Serve the submitted MEI as a file, so a reviewer can open it in an MEI
        viewer before deciding.

        admin_view() only establishes that the caller is staff, so the view
        permission for this model is checked here as well; and a stale link to a
        deleted submission should be a 404, not a 500.
        """
        submission = get_object_or_404(MEISubmission, pk=pk)
        if not self.has_view_permission(request, submission):
            raise PermissionDenied
        response = HttpResponse(submission.mei, content_type="application/xml")
        response["Content-Disposition"] = (
            f'attachment; filename="{submission.mei_filename}"'
        )
        return response

    def save_model(
        self,
        request: HttpRequest,
        obj: MEISubmission,
        form: ModelForm,  # type: ignore[type-arg]
        change: bool,
    ) -> None:
        # The form has already established that this is a legal review outcome.
        chosen = obj.status
        if chosen == form.initial_status:  # type: ignore[attr-defined]
            super().save_model(request, obj, form, change)
            return
        obj.reviewed_by = request.user  # type: ignore[assignment]
        obj.reviewed_at = timezone.now()
        if chosen == SubmissionStatus.PUBLISHED:
            # Publishing is the task's job, including flipping the status, so the
            # row only reads PUBLISHED once the folio really is indexed.
            obj.status = form.initial_status  # type: ignore[attr-defined]
            super().save_model(request, obj, form, change)
            self._queue_publication(request, [obj])
            return
        super().save_model(request, obj, form, change)

    @admin.action(description="Publish selected submissions")
    def publish_submissions(
        self, request: HttpRequest, queryset: QuerySet[MEISubmission]
    ) -> None:
        publishable, skipped = [], []
        for submission in queryset:
            if submission.can_transition_to(SubmissionStatus.PUBLISHED):
                publishable.append(submission)
            else:
                skipped.append(submission)
        if skipped:
            self.message_user(
                request,
                (
                    f"Skipped {len(skipped)} submission(s) that had already been "
                    "reviewed."
                ),
                level=messages.WARNING,
            )
        if not publishable:
            return
        for submission in publishable:
            submission.reviewed_by = request.user  # type: ignore[assignment]
            submission.reviewed_at = timezone.now()
            submission.save()
        self._queue_publication(request, publishable)

    def _queue_publication(
        self, request: HttpRequest, submissions: list[MEISubmission]
    ) -> None:
        for submission in submissions:
            publish_mei_submission_task.apply_async(
                kwargs={
                    # Read by NewTaskResultAdmin to label the task; required.
                    "manuscript_ids": [submission.manuscript_id],
                    "submission_id": submission.pk,
                }
            )
        self.message_user(
            request,
            (
                f"Publishing {len(submissions)} folio(s). Each one is written to the "
                "MEI directory and indexed in the background; check status on the "
                "Task Results page. The folio becomes searchable when its task "
                "succeeds."
            ),
        )


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
admin.site.register(MEISubmission, MEISubmissionAdmin)
admin.site.unregister(TaskResult)
admin.site.register(TaskResult, NewTaskResultAdmin)
