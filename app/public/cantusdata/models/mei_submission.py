import hashlib

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class SubmissionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending review"
    PUBLISHED = "PUBLISHED", "Published"
    CORRECTION_REQUESTED = "CORRECTION_REQUESTED", "Correction requested"
    REFUSED = "REFUSED", "Refused"
    SUPERSEDED = "SUPERSEDED", "Superseded by a newer submission"


# The outcomes an admin may choose for a pending submission. Every other
# transition is refused: a submission is reviewed once, and a correction arrives
# as a new submission rather than as an edit of the old one.
REVIEW_OUTCOMES = (
    SubmissionStatus.PUBLISHED,
    SubmissionStatus.CORRECTION_REQUESTED,
    SubmissionStatus.REFUSED,
)

# Outcomes that must carry an explanation for the submitter.
OUTCOMES_REQUIRING_NOTE = (
    SubmissionStatus.CORRECTION_REQUESTED,
    SubmissionStatus.REFUSED,
)


class MEISubmission(models.Model):
    """
    An MEI file submitted by an external OMR pipeline (Mothra) for one folio.

    A submission arrives PENDING and is invisible to readers. An admin publishes
    it -- which writes the MEI into the live MEI tree and indexes that one folio
    in Solr -- or asks for a correction, or refuses it. Nothing about a
    submission reaches the public site until an admin acts.

    The `mei` column is the authoritative record of what was submitted: it is
    the only copy while the submission is pending, and it stays as the audit
    record after publication, when a copy is also written under
    settings.MEI_FILES_DIR for the indexer to read. Neither copy is ever edited
    in place -- a correction is a new row and a new file -- so they cannot drift.
    """

    class Meta:
        app_label = "cantusdata"
        ordering = ["-submitted_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=SubmissionStatus.values),
                name="mei_submission_status",
            ),
            # Backstop for the view's idempotency check: a retried POST of
            # identical content must not open a second review.
            models.UniqueConstraint(
                fields=["manuscript", "folio_number", "content_sha256"],
                condition=models.Q(status=SubmissionStatus.PENDING),
                name="unique_pending_mei_submission",
            ),
        ]

    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING,
    )
    manuscript = models.ForeignKey("Manuscript", on_delete=models.CASCADE)
    # SET_NULL rather than CASCADE or PROTECT: `import_data chants` deletes and
    # recreates every folio of a manuscript, so PROTECT would break chant
    # re-import and CASCADE would erase review history. folio_number is the
    # denormalized survivor, and is also what Solr keys omr_ngram documents on.
    folio = models.ForeignKey("Folio", on_delete=models.SET_NULL, blank=True, null=True)
    folio_number = models.CharField(
        max_length=50,
        help_text="The canonical folio number, as resolved against the Folio table.",
    )
    mei = models.TextField(help_text="The MEI document, exactly as submitted.")
    content_sha256 = models.CharField(max_length=64, editable=False)
    submitter = models.CharField(
        max_length=150,
        help_text="Username of the submitting user, as asserted by the submitting system.",
    )
    comment = models.TextField(blank=True, help_text="The submitter's note, if any.")
    review_note = models.TextField(
        blank=True,
        help_text=(
            "Shown to the submitter. Required when requesting a correction or "
            "refusing a submission."
        ),
    )
    published_path = models.CharField(
        max_length=512,
        blank=True,
        help_text="Where the MEI was written under MEI_FILES_DIR when published.",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reviewed_mei_submissions",
    )

    def __str__(self) -> str:
        return f"{self.manuscript_id} f. {self.folio_number} from {self.submitter}"

    @staticmethod
    def hash_mei(mei: str) -> str:
        """Return the digest used to recognize a resubmission of identical content."""
        return hashlib.sha256(mei.encode("utf-8")).hexdigest()

    def save(self, *args: object, **kwargs: object) -> None:
        # Computed here as well as in the serializer so the digest can never be
        # left empty by a caller that builds the row directly.
        if self.mei and not self.content_sha256:
            self.content_sha256 = self.hash_mei(self.mei)
        super().save(*args, **kwargs)  # type: ignore[arg-type]

    @property
    def mei_filename(self) -> str:
        """
        The filename to publish this submission under.

        index_manuscript_mei parses the folio number from the segment after the
        last underscore, so only the suffix is load-bearing; the prefix follows
        the convention already used by the curated archive and by Mothra's
        export, and falls back to the manuscript id when a manuscript has no
        siglum to slugify.
        """
        prefix = slugify(self.manuscript.siglum or "") or f"ms{self.manuscript_id}"
        return f"{prefix}_{self.folio_number}.mei"

    def can_transition_to(self, status: str) -> bool:
        """A submission may be reviewed exactly once, out of PENDING."""
        return self.status == SubmissionStatus.PENDING and status in REVIEW_OUTCOMES
