from django.db import models
from django.db.models.signals import post_save, post_delete
from django.utils.text import slugify

from cantusdata.models.folio import Folio
from cantusdata.models.chant import Chant
from cantusdata.models.neume_exemplar import NeumeExemplar

from cantusdata.helpers.signal_wrangler import retrievable_receiver


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
    chant_count = models.IntegerField(default=0)
    public = models.BooleanField(default=False)
    plugins = models.ManyToManyField("cantusdata.Plugin",
                                     related_name="plugins",
                                     blank=True, null=True)

    def __unicode__(self):
        return u"{0} - {1}".format(self.siglum, self.name)

    @property
    def folio_count(self):
        return len(self.folio_set.all())

    @property
    def chant_set(self):
        return Chant.objects.filter(manuscript=self)

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
        return solrconn.query("type:cantusdata_manuscript item_id:{0}"
                              .format(self.id), q_op="AND")

    def add_to_solr(self, solrconn):
        """
        Add a Solr entry for this manuscript if it has chants

        Return true if an entry was added
        """
        # We only want to index the manuscript if it has chants!

        if self.chant_count == 0:
            return False

        solrconn.add(**self.create_solr_record())

        return True

    def delete_from_solr(self, solrconn):
        """
        Delete the Solr entry for this manuscript if it exists

        Return true if there was an entry
        """
        record = self.fetch_solr_records(solrconn)

        if record:
            solrconn.delete(record.results[0]['id'])
            return True

        return False

    def update_chant_count(self):
        """
        Compute the number of chants on the manuscript

        Called by the post_save receiver whenever a folio is changed
        """
        count = 0
        for folio in self.folio_set.all():
            count += folio.chant_count
        self.chant_count = count
        self.save()


@retrievable_receiver(post_save, sender=Folio, dispatch_uid='cantusdata_manuscript_update_chant_count')
def auto_count_chants(sender, instance, **kwargs):
    """
    Compute the number of chants on the folio whenever a chant is saved.
    """
    instance.manuscript.update_chant_count()


@retrievable_receiver(post_save, sender=Manuscript, dispatch_uid='cantusdata_manuscript_solr_add')
def solr_index(sender, instance, created, **kwargs):
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)

    deleted = instance.delete_from_solr(solrconn)
    added = instance.add_to_solr(solrconn)

    if added or deleted:
        solrconn.commit()


@retrievable_receiver(post_delete, sender=Manuscript, dispatch_uid='cantusdata_manuscript_solr_delete')
def solr_delete(sender, instance, **kwargs):
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)

    if instance.delete_from_solr(solrconn):
        solrconn.commit()
