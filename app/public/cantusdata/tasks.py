from cantusdata.celery import app
from django.core.management import call_command


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


@app.task(name="map-folios", bind=True)
def map_folio_task(self, *args, **kwargs):
    call_command(
        "import_folio_mapping",
        manuscripts=[kwargs["manuscript_id"]],
        mapping_data=[kwargs["data"]],
        task=self,
    )
