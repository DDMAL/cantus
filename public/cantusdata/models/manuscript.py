from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, post_delete
from cantusdata.models.folio import Folio
from django.utils.text import slugify


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
    siglum_slug = models.SlugField(max_length=255, unique=True, blank=True,
                                   null=True)
    #reduced max_length, should be safe
    date = models.CharField(max_length=50, blank=True, null=True)
    provenance = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    chant_count = models.IntegerField(default=0)

    def __unicode__(self):
        return u"{0} - {1}".format(self.siglum, self.name)

    @property
    def folio_count(self):
        return len(self.folio_set.all())

    @property
    def chant_set(self):
        chants = list()
        for folio in self.folio_set.all():
            chants += folio.chant_set.all()
        return chants


@receiver(pre_save, sender=Manuscript)
def auto_siglum_slug(sender, instance, **kwargs):
    instance.siglum_slug = slugify(instance.siglum)


@receiver(post_save, sender=Folio)
def auto_count_chants(sender, instance, **kwargs):
    """
    Compute the number of chants on the folio whenever a chant is saved.
    """
    manuscript = instance.manuscript
    count = 0
    for folio in manuscript.folio_set.all():
        count += folio.chant_count
    manuscript.chant_count = count
    manuscript.save()


@receiver(post_save, sender=Manuscript)
def solr_index(sender, instance, created, **kwargs):
    import uuid
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_manuscript item_id:{0}"
                            .format(instance.id), q_op="AND")
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
        'Provenance': manuscript.provenance,
        'Description': manuscript.description
    }
    solrconn.add(**d)
    solrconn.commit()


@receiver(post_delete, sender=Manuscript)
def solr_delete(sender, instance, **kwargs):
    from django.conf import settings
    import solr
    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_manuscript item_id:{0}"
                            .format(instance.id), q_op="AND")
    if record:
        solrconn.delete(record.results[0]['id'])
        solrconn.commit()
