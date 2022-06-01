from django.core.management import call_command
from django.test import TestCase
from cantusdata.models import Manuscript, Concordance, Chant


class ImportAllDataTestCase(TestCase):

    def setUp(self):
        pass

    def test_import_all_data(self):
        call_command('import_data', 'concordances')
        call_command('import_data', 'manuscripts')

    def tearDown(self):
        Chant.objects.all().delete()
        Concordance.objects.all().delete()
        Manuscript.objects.all().delete()
