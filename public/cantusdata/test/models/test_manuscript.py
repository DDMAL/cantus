from django.test import TestCase
from django.db import IntegrityError
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio


class ManuscriptModelTestCase(TestCase):

    first_manuscript = None
    second_manuscript = None

    def setUp(self):
        self.first_manuscript = Manuscript.objects.create(
            name="MyName", siglum=u"    67  a# _ 1*", date="tomorrow",
            provenance="provigo", description="A very nice manuscript...")
        self.second_manuscript = Manuscript.objects.create(name="NumberTwo",
                                                           siglum=u"abcde")

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
        Folio.objects.create(number="123", manuscript=self.first_manuscript)
        self.assertEqual(self.first_manuscript.folio_count, 1)
        # Two folios
        Folio.objects.create(number="456", manuscript=self.first_manuscript)
        self.assertEqual(self.first_manuscript.folio_count, 2)
        # Make sure that a folio from another manuscript doesn't affect count
        self.assertEqual(self.second_manuscript.folio_count, 0)
        Folio.objects.create(number="789", manuscript=self.second_manuscript)
        self.assertEqual(self.second_manuscript.folio_count, 1)
        self.assertEqual(self.first_manuscript.folio_count, 2)
        # First deletion
        Folio.objects.get(number="123").delete()
        self.assertEqual(self.first_manuscript.folio_count, 1)
        # Second deletion
        Folio.objects.get(number="456").delete()
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
        self.assertEqual(set(self.first_manuscript.chant_set), set())
        # One chant
        first_chant = Chant.objects.create(sequence=1,
                                           manuscript=self.first_manuscript,
                                           folio=first_folio)
        self.assertEqual(set(self.first_manuscript.chant_set), {first_chant})
        # Two chants
        second_chant = Chant.objects.create(sequence=2,
                                            manuscript=self.first_manuscript,
                                            folio=first_folio)
        self.assertEqual(set(self.first_manuscript.chant_set),
                         {first_chant, second_chant})
        # Make sure that a chant from another manuscript doesn't affect set
        self.assertEqual(set(self.second_manuscript.chant_set), set())
        third_chant = Chant.objects.create(sequence=3,
                                           manuscript=self.second_manuscript,
                                           folio=second_folio)
        self.assertEqual(set(self.second_manuscript.chant_set),
                         {third_chant})
        self.assertEqual(set(self.first_manuscript.chant_set),
                         {second_chant, first_chant})
        # First deletion
        first_chant.delete()
        self.assertEqual(set(self.first_manuscript.chant_set), {second_chant})
        # Second deletion
        second_chant.delete()
        self.assertEqual(set(self.first_manuscript.chant_set), set())

    def test_siglum_slug(self):
        """
        Test that automatic siglum slug generation works.
        """
        manuscript = Manuscript.objects.get(name="MyName")
        self.assertEqual(manuscript.siglum_slug, u"67-a-_-1")
        # Now we want to try to change the siglum slug
        manuscript.siglum = u"  ano ther @ attmpt"
        manuscript.save()
        self.assertEqual(manuscript.siglum_slug, "ano-ther-attmpt")

    def test_unique_siglum_slug(self):
        """
        Test that the manuscript siglum is unique by asserting that an
        IntegrityError is raised when we try to create a duplicate manuscript.
        """
        with self.assertRaises(IntegrityError):
            Manuscript.objects.create(name="NumberTwo",
                                      siglum=u"    67  a# _ 1*")
