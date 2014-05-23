from django.test import TestCase
from cantusdata.models.chant import Chant


class ChantModelTestCase(TestCase):

    chant = None

    def setUp(self):
        self.chant = Chant()
