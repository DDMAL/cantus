import solr

from django.test import TransactionTestCase
from django.conf import settings

from cantusdata.models.folio import Folio
from cantusdata.models.chant import Chant
from cantusdata.models.manuscript import Manuscript


class FolioModelTestCase(TransactionTestCase):
    fixtures = ["2_initial_data"]

    def setUp(self):
        self.manuscript = Manuscript.objects.get(name="geoff")
        self.folio = Folio.objects.get(number="123")

    def test_unicode(self):
        self.assertEqual(self.folio.__unicode__(), u"123 - , ABC - 456")

    def test_chant_count(self):
        # Folio has one chant from fixture
        self.assertEqual(self.folio.chant_count, 1)
        # We are going to give it another
        chant = Chant.objects.create(sequence=2, manuscript=self.manuscript,
                                     folio=self.folio)
        # After saving the chant, the folio should have 2 chants
        self.assertEqual(self.folio.chant_count, 2)
        # Now we want to try it again and see if we go to 3
        another_chant = Chant.objects.create(sequence=5,
                                             manuscript=self.manuscript,
                                             folio=self.folio)
        # After saving the chant, the folio should now have 3 chants
        self.assertEqual(self.folio.chant_count, 3)
        # Now we test deletes
        chant.delete()
        self.assertEqual(self.folio.chant_count, 2)
        another_chant.delete()
        self.assertEqual(self.folio.chant_count, 1)

    def test_solr_update(self):
        self.folio.number = '9001'

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        prior_resp = self.folio.fetch_solr_records(solrconn)

        self.assertEqual(prior_resp.numFound, 1)
        self.assertNotEqual(prior_resp.results[0]['number'], '9001')

        self.folio.save()

        post_resp = self.folio.fetch_solr_records(solrconn)

        self.assertEqual(post_resp.numFound, 1)
        self.assertEqual(post_resp.results[0]['number'], '9001')

    def test_solr_deletion(self):
        pk = self.folio.pk

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        self.folio.delete_from_solr(solrconn)

        solrconn.commit()

        indexed = solrconn.query('type:cantusdata_folio AND item_id:{}'.format(pk))
        self.assertEqual(indexed.numFound, 0)
