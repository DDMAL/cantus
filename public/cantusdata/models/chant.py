from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete



class Chant(models.Model):
    """
        A Chant belongs to a image page (or a chnat can appear on multiple pages?)
        Feast and Concordances belong to a Chant
        (assuming a chant corresponds to exactly one feast(many-to-one)
        and many-to-many relationship between chants and concordances)
    """
    class Meta:
        app_label = "cantusdata"

    marg = models.CharField(max_length=255, blank=True, null=True)
    folio = models.CharField(max_length=50, blank=True, null=True)
    # sequence can't be blank or null.
    sequence = models.PositiveSmallIntegerField()
    cantusID = models.CharField(max_length=50, blank=True, null=True)
    feast = models.CharField(max_length=255, blank=True, null=True)
    office = models.CharField(max_length=255, blank=True, null=True)
    genre = models.CharField(max_length=255, blank=True, null=True)
    litPosition = models.CharField(max_length=255, blank=True, null=True)
    mode = models.CharField(max_length=255, blank=True, null=True)
    differentia = models.CharField(max_length=255, blank=True, null=True)
    finalis = models.CharField(max_length=255, blank=True, null=True)
    # masterChant ??
    # reference ??
    incipit = models.TextField(blank=True, null=True)
    fullText = models.TextField(blank=True, null=True)
    #concordances = models.ManyToManyField("cantusdata.Concordance",related_name="concordances", default="empty-concordance")
    concordances = models.CharField(max_length=255, blank=True, null=True)
    # not sure about its type
    volpiano = models.CharField(max_length=255, blank=True, null=True)
    manuscript = models.ForeignKey("cantusdata.Manuscript", related_name="chants")

    def __unicode__(self):
        return u"{0}".format(self.cantusID)

@receiver(post_save, sender=Chant)
def solr_index(sender, instance, created, **kwargs):
    import uuid
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_chant item_id:{0}".format(instance.id), q_op="AND")
    if record:
        solrconn.delete(record.results[0]['id'])

    chant = instance
    d = {
        'type': 'cantusdata_chant',
        'id': str(uuid.uuid4()),
        'item_id': chant.id,
        'Marg': chant.marg,
        'Folio': chant.folio,
        'Sequence': chant.sequence,
        'CantusID': chant.cantusID,
        'Feast': chant.feast,
        'Office':chant.office,
        'Genre': chant.genre,
        'Position': chant.litPosition,
        'Mode': chant.mode,
        'Diff': chant.differentia,
        'Finalis': chant.finalis,
        'Incipit': chant.incipit,
        'FullText': chant.fullText,
        'Concordances': chant.concordances
    }
    solrconn.add(**d)
    solrconn.commit()

@receiver(post_delete, sender=Chant)
def solr_delete(sender, instance, **kwargs):
    from django.conf import settings
    import solr
    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_chant item_id:{0}".format(instance.id), q_op="AND")
    solrconn.delete(record.results[0]['id'])
    solrconn.commit()

