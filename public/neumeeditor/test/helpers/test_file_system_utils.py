from django.test import TestCase
from cantusdata.settings import MEDIA_ROOT, MEDIA_URL
from neumeeditor.helpers.file_system_utils import media_url_to_system_path, \
    remove_media_url


class MediaUrlToSystemPathTestCase(TestCase):
    def test_proper_input(self):
        self.assertEquals(media_url_to_system_path(MEDIA_URL + "i/am/a/nice/path.jpeg"), MEDIA_ROOT + "i/am/a/nice/path.jpeg")


class RemoveMediaUrlTestCase(TestCase):
    def test_proper_input(self):
        self.assertEquals(remove_media_url(MEDIA_URL + "i/am/another/great/path"), "i/am/another/great/path")

    def test_improper_input(self):
        """
        Handle the case where the provided url doesn't begin with media URL.
        :return:
        """
        self.assertEquals(remove_media_url("i/don't/include/the/media/url.py"),
                          "i/don't/include/the/media/url.py")
