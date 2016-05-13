from django.db import models
from django.utils.text import slugify

from cantusdata.models.neume_exemplar import NeumeExemplar


class Manuscript(models.Model):
    """The top-level model, representing a particular manuscript

    Folios, chants, feasts, concordances and plugins all belong to a manuscript
    (with some shared among different manuscripts).
    """
    class Meta:
        app_label = "cantusdata"
        ordering = ['name']

    name = models.CharField(max_length=255, blank=True, null=True)
    siglum = models.CharField(max_length=255, blank=True, null=True)
    # siglum_slug = models.SlugField(max_length=255, unique=True, blank=True,
    #                                null=True)
    #reduced max_length, should be safe
    date = models.CharField(max_length=50, blank=True, null=True)
    provenance = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    public = models.BooleanField(default=False)
    plugins = models.ManyToManyField("cantusdata.Plugin",
                                     related_name="plugins",
                                     blank=True, null=True)

    def __unicode__(self):
        return u"{}, {}".format(self.provenance, self.siglum)

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
            'type': 'cantusdata_manuscript',
            'id': str(uuid.uuid4()),
            'item_id': self.id,
            'name': self.name,
            'siglum': self.siglum,
            'siglum_slug': self.siglum_slug,
            'date': self.date,
            'chant_count': self.chant_count,
            'folio_count': self.folio_count,
            'provenance': self.provenance,
            'description': self.description
        }

    def fetch_solr_records(self, solrconn):
        """Query Solr for this object, returning a list of results"""
        return solrconn.query(self._get_solr_query())

    def delete_from_solr(self, solrconn):
        """Delete the Solr entry for this manuscript if it exists"""
        solrconn.delete_query(self._get_solr_query())

    def _get_solr_query(self):
        return "(type:cantusdata_manuscript AND item_id:{0})".format(self.id)
