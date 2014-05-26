from django.test import TestCase
from cantusdata.models.folio import Folio
from cantusdata.models.chant import Chant
from cantusdata.models.manuscript import Manuscript


class FolioModelTestCase(TestCase):

    manuscript = None
    folio = None

    def setUp(self):
        # Generic folio
        self.manuscript = Manuscript.objects.create(siglum=u"ABC - 456",
                                               name="geoff")
        self.folio = Folio.objects.create(number="123",
                                          manuscript=self.manuscript)

    def test_unicode(self):
        self.assertEqual(self.folio.__unicode__(), u"123 - ABC - 456 - geoff")

    def test_chant_count(self):
        # Folio has no chants yet
        self.assertEqual(self.folio.chant_count, 0)
        # We are going to give it a chant
        chant = Chant.objects.create(sequence=2, manuscript=self.manuscript,
                                     folio=self.folio)
        # After saving the chant, the folio should have 1 chant
        self.assertEqual(self.folio.chant_count, 1)
        # Now we want to try it again and see if we go to 2
        second_chant = Chant.objects.create(sequence=5,
                                            manuscript=self.manuscript,
                                            folio=self.folio)
        # After saving the chant, the folio should have 1 chant
        self.assertEqual(self.folio.chant_count, 2)
        # Now we test deletes
        chant.delete()
        self.assertEqual(self.folio.chant_count, 1)
        second_chant.delete()
        self.assertEqual(self.folio.chant_count, 0)

    def tearDown(self):
        """
        It's important that we delete the models in the order of their
        dependancy.
        """
        Chant.objects.all().delete()
        Folio.objects.all().delete()
        Manuscript.objects.all().delete()
