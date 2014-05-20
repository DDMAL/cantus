from django.db import models


class Concordance(models.Model):
    """
    "References to the twelve early manuscripts surveyed in
    volumes 1 and 2 of Corpus Antiphonalium Officii."
    """

    class Meta:
        app_label = "cantusdata"

    letter_code = models.CharField(max_length=1, unique=True, blank=False, null=False)
    institution_city = models.CharField(max_length=255, blank=True, null=True)
    institution_name = models.CharField(max_length=255, blank=True, null=True)
    sections = models.CharField(max_length=255, blank=True, null=True)
    date = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    rism_code = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return u"{0} {1}, {2}, {3} ({4}, from {5}) [RISM: {6}]".format(
            self.letter_code, self.institution_city, self.institution_name,
            self.sections, self.date, self.location, self.rism_code)

    # TODO: Solr indexing