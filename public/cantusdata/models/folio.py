from django.db import models
from django.db.models.signals import post_save, post_delete

from cantusdata.models.chant import Chant
from cantusdata.helpers.signal_wrangler import retrievable_receiver


class Folio(models.Model):
    """
    A folio is a manuscript page.
    A manuscript has many folios.  A folio has many chants.
    """
    class Meta:
        app_label = "cantusdata"
        ordering = ['number']

    number = models.CharField(max_length=50, blank=True, null=True)
    manuscript = models.ForeignKey("Manuscript")
    chant_count = models.IntegerField(default=0)

    def create_solr_record(self):
        """Return a dict representing a new Solr record for this object"""
        import uuid

        return {
            'type': 'cantusdata_folio',
            'id': str(uuid.uuid4()),
            'number': self.number,
            'item_id': self.id,
            'manuscript_id': self.manuscript.id,
        }

    def fetch_solr_records(self, solrconn):
        """Query Solr for this object, returning a list of results"""
        return solrconn.query("type:cantusdata_folio item_id:{0}".format(self.id), q_op="AND")

    def add_to_solr(self, solrconn):
        """
        Add a Solr entry for this folio

        Return true if an entry was added
        """
        solrconn.add(**self.create_solr_record())
        return True

    def delete_from_solr(self, solrconn):
        """
        Delete the Solr entry for this folio if it exists

        Return true if there was an entry
        """
        record = self.fetch_solr_records(solrconn)

        if record:
            solrconn.delete(record.results[0]['id'])
            return True

        return False

    def update_chant_count(self):
        self.chant_count = Chant.objects.filter(folio=self).count()
        self.save()

    def __unicode__(self):
        return u"{0} - {1}".format(self.number, self.manuscript)


@retrievable_receiver(post_delete, sender=Chant, dispatch_uid='cantusdata_folio_decrement_chant_count')
def pre_chant_delete(sender, instance, **kwargs):
    auto_count_chants(instance)


@retrievable_receiver(post_save, sender=Chant, dispatch_uid='cantusdata_folio_increment_chant_count')
def post_chant_save(sender, instance, **kwargs):
    auto_count_chants(instance)


def auto_count_chants(chant):
    """
    Compute the number of chants on the chant's folio
    """
    if chant.folio:
        chant.folio.update_chant_count()


@retrievable_receiver(post_save, sender=Folio, dispatch_uid='cantusdata_folio_solr_add')
def solr_index(sender, instance, created, **kwargs):
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)

    instance.delete_from_solr(solrconn)
    instance.add_to_solr(solrconn)

    solrconn.commit()


@retrievable_receiver(post_delete, sender=Folio, dispatch_uid='cantusdata_folio_solr_delete')
def solr_delete(sender, instance, **kwargs):
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)

    if instance.delete_from_solr(solrconn):
        solrconn.commit()
