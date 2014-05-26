import copy
from django.test import TestCase
from cantusdata.models.chant import Chant
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.folio import Folio


class ChantModelTestCase(TestCase):

    manuscript = None
    folio = None
    chant = None

    def setUp(self):
        self.manuscript = Manuscript.objects.create(name="MyName",
                                siglum=u"    67  a# _ 1*", date="tomorrow",
                                provenance="provigo",
                                description="A very nice manuscript...")
        self.folio = Folio.objects.create(manuscript=self.manuscript,
                                          number="123",)
        self.chant = Chant.objects.create(cantus_id="1234", incipit="5678",
                                          sequence="72", folio=self.folio,
                                          manuscript=self.manuscript)

    def test_unicode(self):
        chant = Chant.objects.get(cantus_id="1234")
        self.assertEqual(chant.__unicode__(), u"1234 - 5678")

    def test_update_solr(self):
        """
        Test that we can update the chant in Solr
        """
        duplicate_chant = copy.deepcopy(self.chant)
        self.assertFalse(self.chant is duplicate_chant)
        self.assertEqual(self.chant.sequence, duplicate_chant.sequence)
        self.chant.sequence = 59
        self.chant.save()
        self.assertNotEqual(self.chant.sequence, duplicate_chant.sequence)

    def tearDown(self):
        """
        It's important that we delete the models in the order of their
        dependancy.
        """
        Chant.objects.all().delete()
        Folio.objects.all().delete()
        Manuscript.objects.all().delete()
