from django.db import models


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
    manuscript = models.ForeignKey('Manuscript')

    def __unicode__(self):
        return u"{0} - {1}".format(self.cantus_id, self.incipit)

    @property
    def concordance_citation_list(self):
        output = []
        for concordance in self.concordances.all():
            output.append(concordance.unicode_citation)
        output.sort()
        return output

    def create_solr_record(self):
        """Return a dict representing a new Solr record for this object"""
        import uuid

        return {
            'type': 'cantusdata_chant',
            'id': str(uuid.uuid4()),
            'item_id': self.id,
            'marginalia': self.marginalia,
            'manuscript': self.manuscript.siglum,
            'manuscript_id': self.manuscript.id,
            'manuscript_name_hidden': self.manuscript.name,
            'public': self.manuscript.public,
            'folio': self.folio.number,
            'folio_id': self.folio.id,
            'image_uri': self.folio.image_uri,
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

    def fetch_solr_records(self, solrconn):
        """Query Solr for this object, returning a list of results"""
        return solrconn.query(self._get_solr_query())

    def delete_from_solr(self, solrconn):
        """Delete the Solr entry for this chant if it exists"""
        solrconn.delete_query(self._get_solr_query())

    def _get_solr_query(self):
        return "(type:cantusdata_chant AND item_id:{0})".format(self.id)
