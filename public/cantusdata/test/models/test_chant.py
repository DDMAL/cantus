from django.test import TestCase
from cantusdata.models.chant import Chant
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.folio import Folio


class ChantModelTestCase(TestCase):

    def setUp(self):
        manuscript = Manuscript.objects.create(name="MyName", siglum=u"    67  a# _ 1*",
                                  date="tomorrow", provenance="provigo",
                                  description="A very nice manuscript...")
        folio = Folio.objects.create(number="123", manuscript=manuscript)
        Chant.objects.create(cantus_id="1234", incipit="5678", sequence="72",
                             manuscript=manuscript, folio=folio)

    def test_unicode(self):
        chant = Chant.objects.get(cantus_id="1234")
        self.assertEqual(chant.__unicode__(), u"1234 - 5678")