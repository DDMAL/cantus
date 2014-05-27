from django.test import TestCase
from cantusdata.models.folio import Folio
from cantusdata.models.chant import Chant
from cantusdata.models.manuscript import Manuscript


class FolioModelTestCase(TestCase):

    fixtures = ["1_users", "2_initial_data"]

    manuscript = None
    folio = None

    def setUp(self):
        self.manuscript = Manuscript.objects.get(name="geoff")
        self.folio = Folio.objects.get(number="123")

    def test_unicode(self):
        self.assertEqual(self.folio.__unicode__(), u"123 - ABC - 456 - geoff")

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

    def tearDown(self):
        """
        It's important that we delete the models in the order of their
        dependancy.
        """
        Chant.objects.all().delete()
        Folio.objects.all().delete()
        Manuscript.objects.all().delete()
