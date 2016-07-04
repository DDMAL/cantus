from django.test import TransactionTestCase
from cantusdata.models.concordance import Concordance


class ConcordanceModelTestCase(TransactionTestCase):
    fixtures = ["2_initial_data"]

    def setUp(self):
        self.concordance = Concordance.objects.get(letter_code="A")

    def test_unicode(self):
        self.assertEqual(self.concordance.__unicode__(), u"A - DDMAL")

    def test_citation(self):
        self.assertEqual(self.concordance.citation,
                             "A  Montreal, DDMAL, ABC123" +
                             " (Today, from Saturn) [RISM: QUE - 982]")
