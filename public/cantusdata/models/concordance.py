from django.db import models
from django.db.models.signals import post_save, post_delete

from cantusdata.helpers.signal_wrangler import retrievable_receiver


class Concordance(models.Model):
    """
    "References to the twelve early manuscripts surveyed in
    volumes 1 and 2 of Corpus Antiphonalium Officii."
    """
    class Meta:
        app_label = "cantusdata"

    letter_code = models.CharField(max_length=1, unique=True,
                                   blank=False, null=False)
    institution_city = models.CharField(max_length=255, blank=True, null=True)
    institution_name = models.CharField(max_length=255, blank=True, null=True)
    library_manuscript_name = models.CharField(max_length=255,
                                               blank=True, null=True)
    date = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    rism_code = models.CharField(max_length=255, blank=True, null=True,
                                 verbose_name="RISM code")

    def __unicode__(self):
        return u"{0} - {1}".format(self.letter_code, self.institution_name)

    @property
    def citation(self):
        return "{0}  {1}, {2}, {3} ({4}, from {5}) [RISM: {6}]".format(
            self.letter_code,
            self.institution_city,
            self.institution_name,
            self.library_manuscript_name,
            self.date,
            self.location,
            self.rism_code
        )

    @property
    def unicode_citation(self):
        return u"{0}  {1}, {2}, {3} ({4}, from {5}) [RISM: {6}]".format(
            self.letter_code,
            self.institution_city,
            self.institution_name,
            self.library_manuscript_name,
            self.date,
            self.location,
            self.rism_code
        )

    def create_solr_record(self):
        """Return a dict representing a new Solr record for this object"""
        import uuid

        return {
            'type': 'cantusdata_concordance',
            'id': str(uuid.uuid4()),
            'item_id': self.id,
            'concordance_citation': self.unicode_citation
        }

    def fetch_solr_records(self, solrconn):
        """Query Solr for this object, returning a list of results"""
        return solrconn.query("type:cantusdata_concordance item_id:{0}"
                              .format(self.id), q_op="AND")

    def add_to_solr(self, solrconn):
        """
        Add a Solr entry for this concordance

        Return true if an entry was added
        """
        solrconn.add(**self.create_solr_record())
        return True

    def delete_from_solr(self, solrconn):
        """
        Delete the Solr entry for this concordance if it exists

        Return true if there was an entry
        """
        record = self.fetch_solr_records()

        if record:
            solrconn.delete(self.results[0]['id'])
            return True

        return False


@retrievable_receiver(post_save, sender=Concordance, dispatch_uid='cantusdata_concordance_solr_add')
def solr_index(sender, instance, created, **kwargs):
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)

    instance.delete_from_solr(solrconn)
    instance.add_to_solr(solrconn)

    solrconn.commit()


@retrievable_receiver(post_delete, sender=Concordance, dispatch_uid='cantusdata_concordance_solr_delete')
def solr_delete(sender, instance, **kwargs):
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)

    if instance.delete_from_solr(solrconn):
        solrconn.commit()
