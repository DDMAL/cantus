from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


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
    rism_code = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        # return self.__str__().decode("utf-8")
        return u"{0}".format(self.letter_code)

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


@receiver(post_save, sender=Concordance)
def solr_index(sender, instance, created, **kwargs):
    import uuid
    from django.conf import settings
    import solr

    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_concordance item_id:{0}"
                            .format(instance.id), q_op="AND")
    if record:
        solrconn.delete(record.results[0]['id'])

    concordance = instance
    # print concordance.__str__()
    d = {
        'type': 'cantusdata_concordance',
        'id': str(uuid.uuid4()),
        'item_id': concordance.id,
        'concordance_citation': concordance.citation.decode("utf-8")
    }
    solrconn.add(**d)
    solrconn.commit()


@receiver(post_delete, sender=Concordance)
def solr_delete(sender, instance, **kwargs):
    from django.conf import settings
    import solr
    solrconn = solr.SolrConnection(settings.SOLR_SERVER)
    record = solrconn.query("type:cantusdata_concordance item_id:{0}"
                            .format(instance.id), q_op="AND")
    if record:
        solrconn.delete(record.results[0]['id'])
        solrconn.commit()
