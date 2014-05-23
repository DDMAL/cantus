from django.test import TestCase
from cantusdata.models.manuscript import Manuscript


class ManuscriptModelTestCase(TestCase):

    def setUp(self):
        Manuscript.objects.create(name="MyName", siglum=u"    67  a# _ 1*",
                                  date="tomorrow", provenance="provigo",
                                  description="A very nice manuscript, if i do"+
                                              "say so myself!",
                                  )

    def test_folio_count(self):
        pass

    def test_chant_set(self):
        pass

    def test_siglum_slug(self):
        manuscript = Manuscript.objects.get(name="MyName")
        self.assertEqual(manuscript.siglum_slug, u"67-a-_-1")
        # Now we want to try to change the siglum slug
        manuscript.siglum = u"  ano ther @ attmpt"
        manuscript.save()
        self.assertEqual(manuscript.siglum_slug, "ano-ther-attmpt")