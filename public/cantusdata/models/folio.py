from django.db import models
from cantusdata.models.chant import Chant
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


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

    def __unicode__(self):
        return u"{0} - {1}".format(self.number, self.manuscript)


@receiver(post_delete, sender=Chant)
def pre_chant_delete(sender, instance, **kwargs):
    auto_count_chants(instance)


@receiver(post_save, sender=Chant)
def post_chant_delete(sender, instance, **kwargs):
    auto_count_chants(instance)


def auto_count_chants(chant):
    """
    Compute the number of chants on the chant's folio
    """
    folio = chant.folio
    if folio:
        folio.chant_count = Chant.objects.filter(folio=folio).count()
        folio.save()


@receiver(post_save, sender=Folio)
def solr_index(sender, instance, created, **kwargs):
    import uuid
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_folio item_id:{0}"
                            .format(instance.id), q_op="AND")
    if record:
        solrconn.delete(record.results[0]['id'])

    folio = instance
    d = {
        'type': 'cantusdata_folio',
        'id': str(uuid.uuid4()),
        'number': folio.number,
        'item_id': folio.id,
        'manuscript_id': folio.manuscript.id,
    }
    solrconn.add(**d)
    solrconn.commit()


@receiver(post_delete, sender=Folio)
def solr_delete(sender, instance, **kwargs):
    from django.conf import settings
    import solr
    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_folio item_id:{0}"
                            .format(instance.id), q_op="AND")
    if record:
        solrconn.delete(record.results[0]['id'])
        solrconn.commit()
