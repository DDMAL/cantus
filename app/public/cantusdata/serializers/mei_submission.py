import re
from typing import Any, Dict

from django.db import transaction
from rest_framework import serializers

from cantusdata.helpers.mei_processing.mei_validation import (
    MEIValidationError,
    validate_mei_document,
)
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.mei_submission import MEISubmission, SubmissionStatus

# Real MEI files for a single folio run to around 120 KB. The cap is generous
# enough for a dense page and small enough that a malformed or misdirected
# request is rejected with a readable error rather than by Django's
# DATA_UPLOAD_MAX_MEMORY_SIZE, which raises a bare SuspiciousOperation.
MAX_MEI_BYTES = 5 * 1024 * 1024


class MEISubmissionStatusSerializer(serializers.ModelSerializer[MEISubmission]):
    """
    The submitter-facing view of a submission: enough to show progress and any
    reviewer feedback, and deliberately without the MEI body.
    """

    manuscript_id = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = MEISubmission
        fields = [
            "id",
            "manuscript_id",
            "folio_number",
            "status",
            "status_display",
            "review_note",
            "comment",
            "submitter",
            "submitted_at",
            "reviewed_at",
        ]
        read_only_fields = fields


class MEISubmissionCreateSerializer(serializers.Serializer[MEISubmission]):
    """
    Accepts one folio's MEI from an external OMR pipeline.

    Everything a submission needs to be reviewable is resolved here, so that a
    row in the review queue is known to name a real manuscript, a real mapped
    folio, and a parseable MEI document.
    """

    manuscript_id = serializers.IntegerField()
    folio_number = serializers.CharField(max_length=50)
    mei = serializers.CharField(trim_whitespace=False)
    submitter = serializers.CharField(max_length=150)
    comment = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=True
    )

    def validate_mei(self, value: str) -> str:
        size = len(value.encode("utf-8"))
        if size > MAX_MEI_BYTES:
            raise serializers.ValidationError(
                f"MEI document is {size} bytes; the maximum accepted is "
                f"{MAX_MEI_BYTES} bytes."
            )
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        manuscript = self._resolve_manuscript(attrs["manuscript_id"])
        folio = self._resolve_folio(manuscript, attrs["folio_number"])
        self._validate_mei_content(attrs["mei"])
        attrs["manuscript"] = manuscript
        attrs["folio"] = folio
        # The canonical spelling, which is what the indexer and Solr use. A
        # submitter sending "1r" gets the manuscript's own "001r" stored.
        attrs["folio_number"] = folio.number
        attrs["content_sha256"] = MEISubmission.hash_mei(attrs["mei"])
        return attrs

    def _resolve_manuscript(self, manuscript_id: int) -> Manuscript:
        # Deliberately not filtered on `public`: manuscripts being processed by
        # an OMR pipeline are normally still unpublished, and that is the case
        # this endpoint exists to serve.
        try:
            return Manuscript.objects.get(pk=manuscript_id)
        except Manuscript.DoesNotExist:
            raise serializers.ValidationError(
                {"manuscript_id": f"No manuscript with id {manuscript_id}."}
            ) from None

    def _resolve_folio(self, manuscript: Manuscript, folio_number: str) -> Folio:
        # Leading zeros are matched loosely, as in views/folio.py, because folio
        # numbers are strings and callers pad them inconsistently. The submitted
        # value is escaped before it reaches the pattern: unescaped, a caller
        # could send regex metacharacters and resolve to a folio they did not
        # name.
        folios = Folio.objects.filter(
            manuscript=manuscript,
            number__iregex=r"^0*{0}$".format(re.escape(folio_number.strip())),
        ).order_by("number")
        folio = folios.first()
        if folio is None:
            raise serializers.ValidationError(
                {
                    "folio_number": (
                        f"Manuscript {manuscript.pk} has no folio {folio_number}. "
                        "Import the manuscript's chants first, which creates its "
                        "folios."
                    )
                }
            )
        if not folio.image_uri:
            # index_manuscript_mei cannot distinguish this from a missing folio:
            # it would create a duplicate Folio row and index n-grams with an
            # empty image_uri, which are searchable but impossible to locate on
            # the page. Refuse now, while the submitter can still act on it.
            raise serializers.ValidationError(
                {
                    "folio_number": (
                        f"Folio {folio.number} of manuscript {manuscript.pk} is not "
                        "mapped to an image yet, so its notation could not be "
                        "displayed. Map the manuscript's folios first."
                    )
                }
            )
        return folio

    def _validate_mei_content(self, mei: str) -> None:
        try:
            validate_mei_document(mei)
        except MEIValidationError as exc:
            raise serializers.ValidationError({"mei": str(exc)}) from exc

    def find_duplicate(self) -> MEISubmission | None:
        """
        The pending submission this one would duplicate, if there is one.

        Lets a retried POST of identical content return the existing review
        rather than opening a second one.
        """
        data = self.validated_data
        return MEISubmission.objects.filter(
            manuscript=data["manuscript"],
            folio_number=data["folio_number"],
            content_sha256=data["content_sha256"],
            status=SubmissionStatus.PENDING,
        ).first()

    def create(self, validated_data: Dict[str, Any]) -> MEISubmission:
        with transaction.atomic():
            # One live row per folio in the review queue: an earlier pending
            # submission for the same folio is history, not a second thing to
            # review.
            MEISubmission.objects.filter(
                manuscript=validated_data["manuscript"],
                folio_number=validated_data["folio_number"],
                status=SubmissionStatus.PENDING,
            ).update(status=SubmissionStatus.SUPERSEDED)
            return MEISubmission.objects.create(
                manuscript=validated_data["manuscript"],
                folio=validated_data["folio"],
                folio_number=validated_data["folio_number"],
                mei=validated_data["mei"],
                content_sha256=validated_data["content_sha256"],
                submitter=validated_data["submitter"],
                comment=validated_data.get("comment", ""),
                status=SubmissionStatus.PENDING,
            )
