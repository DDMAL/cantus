from django.db import models
from django.db.models.signals import post_save, post_delete

from cantusdata.models.concordance import Concordance

from cantusdata.helpers.signal_wrangler import retrievable_receiver


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
    sequence = models.PositiveSmallIntegerField()
    cantus_id = models.CharField(max_length=50, blank=True, null=True)
    feast = models.CharField(max_length=255, blank=True, null=True)
    office = models.CharField(max_length=255, blank=True, null=True)
    genre = models.CharField(max_length=255, blank=True, null=True)
    lit_position = models.CharField(max_length=255, blank=True, null=True)
    mode = models.CharField(max_length=255, blank=True, null=True)
    differentia = models.CharField(max_length=255, blank=True, null=True)
    finalis = models.CharField(max_length=255, blank=True, null=True)
    incipit = models.TextField(blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)
    concordances = models.ManyToManyField("cantusdata.Concordance",
                                          related_name="concordances",
                                          blank=True)
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

    def add_to_solr(self, solrconn):
        """
        Add a Solr entry for this chant

        Return true
        """
        import uuid

        d = {
            'type': 'cantusdata_chant',
            'id': str(uuid.uuid4()),
            'item_id': self.id,
            'marginalia': self.marginalia,
            'manuscript': self.manuscript.siglum,
            'manuscript_id': self.manuscript.id,
            'manuscript_name_hidden': self.manuscript.name,
            'folio': self.folio.number,
            'folio_id': self.folio.id,
            'sequence': self.sequence,
            'cantus_id': self.cantus_id,
            'feast': self.feast,
            'office': self.office,
            'genre': self.genre,
            'position': self.lit_position,
            'mode': self.mode,
            'differentia': self.differentia,
            'finalis': self.finalis,
            'incipit': self.incipit,
            'full_text': self.full_text,
            'volpiano': self.volpiano,
            'concordances': self.concordance_citation_list
        }

        solrconn.add(**d)
        return True

    def delete_from_solr(self, solrconn):
        """
        Delete the Solr entry for this chant if it exists

        Return true if there was an entry
        """
        record = solrconn.query("type:cantusdata_chant item_id:{0}"
                                .format(self.id), q_op="AND")

        if record:
            solrconn.delete(self.results[0]['id'])
            return True

        return False


@retrievable_receiver(post_save, sender=Chant, dispatch_uid='cantusdata_chant_solr_add')
def solr_index(sender, instance, created, **kwargs):
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)

    instance.delete_from_solr(solrconn)
    instance.add_to_solr(solrconn)

    solrconn.commit()


@retrievable_receiver(post_delete, sender=Chant, dispatch_uid='cantusdata_chant_solr_delete')
def solr_delete(sender, instance, **kwargs):
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)

    if instance.delete_from_solr(solrconn):
        solrconn.commit()
