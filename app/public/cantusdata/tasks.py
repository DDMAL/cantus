import os
import tempfile

from cantusdata.celery import app
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from celery.signals import task_received
from django_celery_results.models import TaskResult

# Attached to a manuscript when its notation is first published, because the
# client only renders the notation-search fields for manuscripts carrying these
# plugins -- indexing alone surfaces nothing to a reader.
#
# Named as the admin and README name them. What the client matches on is the
# slug (Manuscript's serializer exposes plugins by slug, and OMRSearchProvider
# looks for "neume-search"/"pitch-search"), so plugins are resolved by slug
# below: deployments already carry rows whose names are the slugs themselves,
# and keying on the name would add a second row with the same slug instead of
# reusing the one that is already there.
NOTATION_SEARCH_PLUGINS = ("Neume Search", "Pitch Search")


@app.task(name="import-chants", bind=True)
def chant_import_task(self, *args, **kwargs):
    manuscript_ids = kwargs["manuscript_ids"]
    for man_id in manuscript_ids:
        call_command(
            "import_data",
            "chants",
            f"--manuscript-id={man_id}",
            task=self,
        )


@app.task(name="publish-mei-submission", bind=True)
def publish_mei_submission_task(self, *args, **kwargs):
    """
    Publish one reviewed MEI submission: write the file, index the folio, reveal it.

    kwargs:
        manuscript_ids: [<manuscript id>] -- every task in this module passes
            this key, and the Task Results admin reads it out of task_kwargs to
            label the row, so it is required rather than decorative.
        submission_id: the MEISubmission to publish.

    The file is written before indexing on purpose: a failed index can be retried
    from the file that is already on the volume, whereas a successful index with
    no file would leave the MEI tree incomplete for the next full reindex.
    """
    # Imported here rather than at module scope: this module is imported by
    # Celery at startup, before the app registry is necessarily ready.
    from cantusdata.models.mei_submission import MEISubmission, SubmissionStatus

    submission = MEISubmission.objects.select_related("manuscript").get(
        pk=kwargs["submission_id"]
    )
    manuscript = submission.manuscript

    published_path = write_submission_to_mei_dir(submission)

    call_command(
        "index_manuscript_mei",
        str(manuscript.pk),
        "--folio",
        submission.folio_number,
        "--replace",
        "--mei-dir",
        settings.MEI_FILES_DIR,
    )

    for plugin_name in NOTATION_SEARCH_PLUGINS:
        manuscript.plugins.add(get_plugin_by_slug(plugin_name))

    submission.status = SubmissionStatus.PUBLISHED
    submission.published_path = published_path
    submission.reviewed_at = submission.reviewed_at or timezone.now()
    submission.save()
    return {"submission_id": submission.pk, "published_path": published_path}


def get_plugin_by_slug(plugin_name):
    """
    The Plugin whose slug matches `plugin_name`, created with that name if none.

    Plugin.slug is a property rather than a column, so the match happens in
    Python -- the table holds a handful of rows. Matching on the slug rather than
    the name is what stops a second row with the same slug being created next to
    one that already exists under a different spelling.
    """
    from django.utils.text import slugify

    from cantusdata.models.plugin import Plugin

    wanted = slugify(plugin_name)
    for plugin in Plugin.objects.all():
        if plugin.slug == wanted:
            return plugin
    return Plugin.objects.create(name=plugin_name)


def find_mei_file_for_folio(manuscript_dir, folio_number):
    """
    The existing MEI file in `manuscript_dir` for `folio_number`, if there is one.

    index_manuscript_mei reads the folio from the segment after the last
    underscore, so files with unrelated prefixes -- the curated archive's
    "CDN-Hsmu_M2149.L4_034r.mei" and a published deposit's
    "cdn-hsmu-m2149l4_034r.mei" -- name the same folio and would both be indexed.
    Publishing therefore reuses whatever filename is already there instead of
    adding a second one.
    """
    if not os.path.isdir(manuscript_dir):
        return None
    matches = [
        name
        for name in sorted(os.listdir(manuscript_dir))
        if name.endswith(".mei") and name.split("_")[-1].split(".")[0] == folio_number
    ]
    if len(matches) > 1:
        raise RuntimeError(
            f"{manuscript_dir} already holds {len(matches)} MEI files for folio "
            f"{folio_number} ({', '.join(matches)}). Indexing would count that "
            "folio more than once; remove the duplicates before publishing."
        )
    return matches[0] if matches else None


def write_submission_to_mei_dir(submission):
    """
    Write a submission's MEI into the live MEI tree, returning the path written.

    Written to a temporary name in the destination directory and moved into
    place, so a concurrent indexing run never reads a half-written file.
    """
    manuscript_dir = os.path.join(settings.MEI_FILES_DIR, str(submission.manuscript_id))
    os.makedirs(manuscript_dir, exist_ok=True)
    # Replace the folio's existing file, under its existing name, so the tree
    # keeps exactly one MEI file per folio.
    existing_name = find_mei_file_for_folio(manuscript_dir, submission.folio_number)
    destination = os.path.join(manuscript_dir, existing_name or submission.mei_filename)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=manuscript_dir,
        prefix=".incoming-",
        suffix=".mei",
        delete=False,
    ) as staged:
        staged.write(submission.mei)
        staged_path = staged.name
    try:
        os.replace(staged_path, destination)
    except OSError:
        os.unlink(staged_path)
        raise
    return destination


@app.task(name="map-folios", bind=True)
def map_folio_task(self, *args, **kwargs):
    call_command(
        "import_folio_mapping",
        manuscripts=[kwargs["manuscript_ids"]],
        mapping_data=[kwargs["data"]],
        task=self,
    )


@task_received.connect
def task_received_handler(sender=None, headers=None, body=None, **kwargs):
    request = kwargs["request"]
    TaskResult.objects.store_result(
        request.content_type,
        request.content_encoding,
        request.task_id,
        "",
        "RECEIVED",
        task_args=request.args,
        task_kwargs=request.kwargs,
        task_name=request.task_name,
        worker=sender,
    )
