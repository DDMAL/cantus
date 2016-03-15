import solr

from django.test import TransactionTestCase
from django.conf import settings

from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio


class ManuscriptModelTestCase(TransactionTestCase):
    fixtures = ["2_initial_data"]

    def setUp(self):
        self.first_manuscript = Manuscript.objects.get(name="MyName")
        self.second_manuscript = Manuscript.objects.get(name="NumberTwo")

    def test_unicode(self):
        self.assertEqual(self.first_manuscript.__unicode__(),
                         "    67  a# _ 1* - MyName")

    def test_folio_count(self):
        """
        Test that the manuscript folio count is updated correctly.
        """
        # No folios
        self.assertEqual(self.first_manuscript.folio_count, 0)
        # One folio
        Folio.objects.create(number="I", manuscript=self.first_manuscript)
        self.assertEqual(self.first_manuscript.folio_count, 1)
        # Two folios
        Folio.objects.create(number="II", manuscript=self.first_manuscript)
        self.assertEqual(self.first_manuscript.folio_count, 2)
        # Make sure that a folio from another manuscript doesn't affect count
        self.assertEqual(self.second_manuscript.folio_count, 0)
        Folio.objects.create(number="III", manuscript=self.second_manuscript)
        self.assertEqual(self.second_manuscript.folio_count, 1)
        self.assertEqual(self.first_manuscript.folio_count, 2)
        # First deletion
        Folio.objects.get(number="I").delete()
        self.assertEqual(self.first_manuscript.folio_count, 1)
        # Second deletion
        Folio.objects.get(number="II").delete()
        self.assertEqual(self.first_manuscript.folio_count, 0)

    def test_chant_set(self):
        """
        Test that the manuscript chant set is updated correctly.
        """
        first_folio = Folio.objects.create(number="f1",
                                           manuscript=self.first_manuscript)
        second_folio = Folio.objects.create(number="f2",
                                            manuscript=self.second_manuscript)
        # No chants
        self.assertEqual(set(self.first_manuscript.chant_set.all()), set())
        # One chant
        first_chant = Chant.objects.create(sequence=1,
                                           manuscript=self.first_manuscript,
                                           folio=first_folio)
        self.assertEqual(set(self.first_manuscript.chant_set.all()), {first_chant})
        # Two chants
        second_chant = Chant.objects.create(sequence=2,
                                            manuscript=self.first_manuscript,
                                            folio=first_folio)
        self.assertEqual(set(self.first_manuscript.chant_set.all()),
                         {first_chant, second_chant})
        # Make sure that a chant from another manuscript doesn't affect set
        self.assertEqual(set(self.second_manuscript.chant_set.all()), set())
        third_chant = Chant.objects.create(sequence=3,
                                           manuscript=self.second_manuscript,
                                           folio=second_folio)
        self.assertEqual(set(self.second_manuscript.chant_set.all()),
                         {third_chant})
        self.assertEqual(set(self.first_manuscript.chant_set.all()),
                         {second_chant, first_chant})
        # First deletion
        first_chant.delete()
        self.assertEqual(set(self.first_manuscript.chant_set.all()), {second_chant})
        # Second deletion
        second_chant.delete()
        self.assertEqual(set(self.first_manuscript.chant_set.all()), set())

    def test_solr_update(self):
        ms = self.first_manuscript
        ms.name = 'I am the best book'

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        prior_resp = ms.fetch_solr_records(solrconn)

        self.assertEqual(prior_resp.numFound, 1)
        self.assertNotEqual(prior_resp.results[0]['name'], 'I am the best book')

        ms.save()

        post_resp = ms.fetch_solr_records(solrconn)

        self.assertEqual(post_resp.numFound, 1)
        self.assertEqual(post_resp.results[0]['name'], 'I am the best book')

    def test_solr_deletion(self):
        pk = self.first_manuscript.pk

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        self.first_manuscript.delete_from_solr(solrconn)

        solrconn.commit()

        indexed = solrconn.query('type:cantusdata_manuscript AND item_id:{}'.format(pk))
        self.assertEqual(indexed.numFound, 0)
