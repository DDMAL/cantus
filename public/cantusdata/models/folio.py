from django.db import models


class Folio(models.Model):
    """
    A folio is a manuscript page.
    A manuscript has many folios.  A folio has many chants.
    """
    class Meta:
        app_label = "cantusdata"
        ordering = ['number']

    number = models.CharField(max_length=50, blank=True, null=True)
    image_uri = models.CharField(max_length=255, blank=True, null=True)
    manuscript = models.ForeignKey("Manuscript")

    @property
    def chant_count(self):
        return self.chant_set.count()

    def create_solr_record(self):
        """Return a dict representing a new Solr record for this object"""
        import uuid

        return {
            'type': 'cantusdata_folio',
            'id': str(uuid.uuid4()),
            'number': self.number,
            'item_id': self.id,
            'image_uri': self.image_uri,
            'manuscript_id': self.manuscript.id,
        }

    def fetch_solr_records(self, solrconn):
        """Query Solr for this object, returning a list of results"""
        return solrconn.query(self._get_solr_query())

    def delete_from_solr(self, solrconn):
        """Delete the Solr entry for this folio if it exists"""
        solrconn.delete_query(self._get_solr_query())

    def _get_solr_query(self):
        return "(type:cantusdata_folio AND item_id:{0})".format(self.id)

    def __str__(self):
        return "{0} - {1}".format(self.number, self.manuscript)
