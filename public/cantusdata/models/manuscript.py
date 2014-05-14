from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete


class Manuscript(models.Model):
    """
        A Manuscript is the top-level model, 
        Pages, Chants, Feasts and Concordances belong to a Manuscript
        (some may be shared among different manuscripts?)
    """
    class Meta:
        app_label = "cantusdata"

    name = models.CharField(max_length=255, blank=True, null=True)
    siglum = models.CharField(max_length=255, blank=True, null=True)
    #reduced max_length, should be safe
    date = models.CharField(max_length=50, blank=True, null=True)
    provenance = models.CharField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return u"{0}".format(self.siglum)

# maybe a function to get tht total number of chants in a manuscript

#    @property
#    def chant_count(self):
#        for p in self.pages:
#            for c in p.getChants

@receiver(post_save, sender=Manuscript)
def solr_index(sender, instance, created, **kwargs):
    import uuid
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_manuscript item_id:{0}".format(instance.id), q_op="AND")
    if record:
        solrconn.delete(record.results[0]['id'])
    manuscript = instance
    d = {
        'type': 'cantusdata_manuscript',
        'id': str(uuid.uuid4()),
        'item_id': manuscript.id,
        'Name': manuscript.name,
        'Siglum': manuscript.siglum,
        'Date': manuscript.date,
        'Provenance': manuscript.provenance
    }
    solrconn.add(**d)
    solrconn.commit()

@receiver(post_delete, sender=Manuscript)
def solr_delete(sender, instance, **kwargs):
    from django.conf import settings
    import solr
    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_manuscript item_id:{0}".format(instance.id), q_op="AND")
    solrconn.delete(record.results[0]['id'])
    solrconn.commit()

