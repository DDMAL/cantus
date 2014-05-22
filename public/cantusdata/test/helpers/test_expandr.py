from django.test import TestCase
from cantusdata.helpers.expandr import PositionExpander


class TestPositionExpander(TestCase):

    position_expander = None

    def setUp(self):
        self.position_expander = PositionExpander()

    def test_get_text(self):
        output = self.position_expander.get_text("E", "A", "4")
        self.assertEqual("4th Antiphon for the Magnificat or Benidictus", output)
