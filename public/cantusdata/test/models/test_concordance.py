import copy
from django.test import TestCase
from cantusdata.models.concordance import Concordance


class ConcordanceModelTestCase(TestCase):

    concordance = None

    def setUp(self):
        self.concordance = Concordance.objects.create(letter_code="A",
                                   institution_city="Montreal",
                                   institution_name="DDMAL",
                                   library_manuscript_name="ABC123",
                                   date="Today",
                                   location="Saturn",
                                   rism_code="QUE - 982")

    def test_unicode(self):
        self.assertEqual(self.concordance.__unicode__(), u"A - DDMAL")

    def test_citation(self):
        self.assertEqual(self.concordance.citation,
                             "A  Montreal, DDMAL, ABC123" +
                             " (Today, from Saturn) [RISM: QUE - 982]")

    def test_update_solr(self):
        """
        Test that we can update the concordance in Solr.
        """
        duplicate_concordance = copy.deepcopy(self.concordance)
        self.assertFalse(self.concordance is duplicate_concordance)
        self.assertEqual(self.concordance.institution_city,
                         duplicate_concordance.institution_city)
        self.concordance.institution_city = "Toronto"
        self.concordance.save()
        self.assertNotEqual(self.concordance.institution_city,
                            duplicate_concordance.institution_city)

    def tearDown(self):
        Concordance.objects.all().delete()
