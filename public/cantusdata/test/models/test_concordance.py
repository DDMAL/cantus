from django.test import TestCase
from cantusdata.models.concordance import Concordance


class ConcordanceModelTestCase(TestCase):

    def setUp(self):
        Concordance.objects.create(letter_code="A",
                                   institution_city="Montreal",
                                   institution_name="DDMAL",
                                   library_manuscript_name="ABC123",
                                   date="Today",
                                   location="Saturn",
                                   rism_code="QUE - 982")

    def test_unicode(self):
        concordance = Concordance.objects.get(letter_code="A")
        self.assertEqual(concordance.__unicode__(), u"A - DDMAL")

    def test_citation(self):
        concordance = Concordance.objects.get(letter_code="A")
        self.assertEqual(concordance.citation,
                             "A  Montreal, DDMAL, ABC123" +
                             " (Today, from Saturn) [RISM: QUE - 982]")
