from django.core.management import call_command
from django.test import TestCase
from cantusdata.models import Manuscript, Concordance, Chant


class ImportAllDataTestCase(TestCase):

    def setUp(self):
        pass

    def test_import_all_data(self):
        call_command('import_manuscript_data', 'test/test_manuscripts.csv')
        call_command('import_concordance_data', 'test/test_concordances')
        call_command('import_chant_data', 'test/test_chants.csv')

    def test_import_manuscript_errors(self):
        # File doesn't exist
        with self.assertRaisesMessage(NameError, 'Please provide a file name!'):
            call_command('import_manuscript_data', '')
        # File doesn't exist
        with self.assertRaisesMessage(IOError, 'File blahblahblah does not exist!'):
            call_command('import_manuscript_data', 'blahblahblah')

    def test_import_concordance_errors(self):
        # File doesn't exist
        with self.assertRaisesMessage(NameError, 'Please provide a file name!'):
            call_command('import_concordance_data', '')
        # File doesn't exist
        with self.assertRaisesMessage(IOError, 'File blahblahblah does not exist!'):
            call_command('import_concordance_data', 'blahblahblah')

    def test_import_chant_errors(self):
        # File doesn't exist
        with self.assertRaisesMessage(NameError, 'Please provide a file name!'):
            call_command('import_chant_data', '')
        # File doesn't exist
        with self.assertRaisesMessage(IOError, 'File blahblahblah does not exist!'):
            call_command('import_chant_data', 'blahblahblah')

    def tearDown(self):
        Chant.objects.all().delete()
        Concordance.objects.all().delete()
        Manuscript.objects.all().delete()
