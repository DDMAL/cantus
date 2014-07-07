from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from cantusdata.models.concordance import Concordance


class Chant(models.Model):
    """
        A Chant belongs to a image page (or a chant can appear
        on multiple pages?)
        Feast and Concordances belong to a Chant
        (assuming a chant corresponds to exactly one feast(many-to-one)
        and many-to-many relationship between chants and concordances)
    """
    class Meta:
        app_label = "cantusdata"
        ordering = ['sequence']

    marginalia = models.CharField(max_length=255, blank=True, null=True)
    folio = models.ForeignKey("cantusdata.Folio", blank=True, null=True)
    # sequence can't be blank or null.
    sequence = models.PositiveSmallIntegerField()
    cantus_id = models.CharField(max_length=50, blank=True, null=True)
    feast = models.CharField(max_length=255, blank=True, null=True)
    office = models.CharField(max_length=255, blank=True, null=True)
    genre = models.CharField(max_length=255, blank=True, null=True)
    lit_position = models.CharField(max_length=255, blank=True, null=True)
    mode = models.CharField(max_length=255, blank=True, null=True)
    differentia = models.CharField(max_length=255, blank=True, null=True)
    finalis = models.CharField(max_length=255, blank=True, null=True)
    # masterChant ??
    # reference ??
    incipit = models.TextField(blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)
    concordances = models.ManyToManyField(
        "cantusdata.Concordance", related_name="concordances",
        default="empty-concordance")
    # not sure about its type
    volpiano = models.TextField(blank=True, null=True)
    manuscript = models.ForeignKey("cantusdata.Manuscript",
                                   related_name="chants")

    def __unicode__(self):
        return u"{0} - {1}".format(self.cantus_id, self.incipit)

    @property
    def concordance_citation_list(self):
        output = []
        for concordance in self.concordances.all():
            output.append(concordance.unicode_citation)
        output.sort()
        return output

@receiver(post_save, sender=Chant)
def solr_index(sender, instance, created, **kwargs):
    import uuid
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_chant item_id:{0}"
                            .format(instance.id), q_op="AND")
    if record:
        solrconn.delete(record.results[0]['id'])

    chant = instance
    d = {
        'type': 'cantusdata_chant',
        'id': str(uuid.uuid4()),
        'item_id': chant.id,
        'marginalia': chant.marginalia,
        'manuscript': chant.manuscript.siglum,
        'manuscript_id': chant.manuscript.id,
        'manuscript_name_hidden': chant.manuscript.name,
        'folio': chant.folio.number,
        'folio_id': chant.folio.id,
        'sequence': chant.sequence,
        'cantus_id': chant.cantus_id,
        'feast': chant.feast,
        'office': chant.office,
        'genre': chant.genre,
        'position': chant.lit_position,
        'mode': chant.mode,
        'differentia': chant.differentia,
        'finalis': chant.finalis,
        'incipit': chant.incipit,
        'full_text': chant.full_text,
        'volpiano': chant.volpiano,
        'concordances': chant.concordance_citation_list
    }
    solrconn.add(**d)
    solrconn.commit()


@receiver(post_delete, sender=Chant)
def solr_delete(sender, instance, **kwargs):
    from django.conf import settings
    import solr
    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_chant item_id:{0}"
                            .format(instance.id), q_op="AND")
    if record:
        solrconn.delete(record.results[0]['id'])
        solrconn.commit(
)