from django.test import TransactionTestCase
from cantusdata.models.plugin import Plugin
from cantusdata.models.manuscript import Manuscript


class FolioModelTestCase(TransactionTestCase):
    fixtures = ["2_initial_data"]

    def setUp(self):
        self.first_plugin = Plugin(name="A very nice plugin!")
        self.first_plugin.save()
        self.second_plugin = Plugin(name="Another great plugin.")
        self.second_plugin.save()
        self.manuscript = Manuscript.objects.get(name="geoff")

    def test_unicode(self):
        self.assertEqual(self.first_plugin.__str__(),
                         "A very nice plugin!")
        self.assertEqual(self.second_plugin.__str__(),
                         "Another great plugin.")

    def test_slug(self):
        self.assertEqual(self.first_plugin.slug,
                         "a-very-nice-plugin")
        self.assertEqual(self.second_plugin.slug,
                         "another-great-plugin")

    def test_manuscript_attachment(self):
        # Geoff doesn't have any Plugins yet
        self.assertEqual(len(self.manuscript.plugins.all()), 0)
        # Add the first Plugin
        self.manuscript.plugins.add(self.first_plugin)
        self.assertEqual(len(self.manuscript.plugins.all()), 1)
        # Add the second
        self.manuscript.plugins.add(self.second_plugin)
        self.assertEqual(len(self.manuscript.plugins.all()), 2)
        # Clear em
        self.manuscript.plugins.clear()
        self.assertEqual(len(self.manuscript.plugins.all()), 0)
