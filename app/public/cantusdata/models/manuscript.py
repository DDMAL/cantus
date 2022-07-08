from django.db import models
from django.core.management import call_command
from django.utils.text import slugify
import threading

from cantusdata.models.neume_exemplar import NeumeExemplar

class IsMapped(models.TextChoices):
    UNMAPPED = "UNMAPPED", "Unmapped"
    PENDING = "PENDING", "Pending"
    MAPPED = "MAPPED", "Mapped"
    
class Manuscript(models.Model):
    """The top-level model, representing a particular manuscript

    Folios, chants, feasts, concordances and plugins all belong to a manuscript
    (with some shared among different manuscripts).
    """

    class Meta:
        app_label = "cantusdata"
        ordering = ["name"]
        constraints = [models.CheckConstraint(check = models.Q(is_mapped__in = IsMapped.values), name = "is_mapped_status")]

    name = models.CharField(max_length=255, blank=True, null=True)
    siglum = models.CharField(max_length=255, blank=True, null=True)
    date = models.CharField(max_length=50, blank=True, null=True)
    provenance = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    public = models.BooleanField(default=False)
    is_mapped = models.CharField(max_length=10, choices=IsMapped.choices)
    chants_loaded = models.BooleanField(default=False)
    plugins = models.ManyToManyField(
        "cantusdata.Plugin", related_name="plugins", blank=True
    )

    cantus_url = models.CharField(max_length=255, blank=True, null=True)
    csv_export_url = models.CharField(max_length=255, blank=True, null=True)
    manifest_url = models.CharField(max_length=255, blank=True, null=True)

    # Store the initial value of public in order to detect any changes.
    def __init__(self, *args, **kwargs):
        super(Manuscript, self).__init__(*args, **kwargs)
        self._last_public_value = self.public

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        super(Manuscript, self).save(force_insert, force_update, *args, **kwargs)

        if (self.public != self._last_public_value) and self.chants_loaded:
            # The public property has changed, we need to refresh the Solr chants
            thread = threading.Thread(
                target=call_command,
                args=("refresh_solr", "chants", str(self.id)),
                kwargs={},
            )
            thread.start()
            self._last_public_value = self.public

    def __str__(self):
        return "{}, {}".format(self.provenance, self.siglum)

    @property
    def folio_count(self):
        return self.folio_set.count()

    @property
    def chant_count(self):
        return self.chant_set.count()

    @property
    def siglum_slug(self):
        return slugify(self.siglum)

    @property
    def neume_exemplars(self):
        return NeumeExemplar.objects.filter(folio__manuscript=self)

    def create_solr_record(self):
        """Return a dict representing a new Solr record for this object"""
        import uuid

        return {
            "type": "cantusdata_manuscript",
            "id": str(uuid.uuid4()),
            "item_id": self.id,
            "name": self.name,
            "siglum": self.siglum,
            "siglum_slug": self.siglum_slug,
            "date": self.date,
            "public": self.public,
            "chant_count": self.chant_count,
            "folio_count": self.folio_count,
            "provenance": self.provenance,
            "description": self.description,
        }

    def fetch_solr_records(self, solrconn):
        """Query Solr for this object, returning a list of results"""
        return solrconn.query(self._get_solr_query())

    def delete_from_solr(self, solrconn):
        """Delete the Solr entry for this manuscript if it exists"""
        solrconn.delete_query(self._get_solr_query())

    def _get_solr_query(self):
        return "(type:cantusdata_manuscript AND item_id:{0})".format(self.id)
