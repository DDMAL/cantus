from lxml import etree
from django.test import TestCase
from cantusdata.settings import MEDIA_ROOT, BASE_DIR
from neumeeditor.helpers.gamera_xml_importer import RunLengthImage, GameraXML, \
    import_gamera_file, strip_neume_name


# class NeumeNameStripperTestCase(TestCase):
#     def test_does_begin(self):
#         self.assertEquals(strip_neume_name("neume.some.other.stuff"), "some.other.stuff")
#
#     def test_does_not_begin(self):
#         self.assertEquals(strip_neume_name("other.stuff"), "other.stuff")
from neumeeditor.helpers.mei_importer import import_mei_file, Neume


class MEIImportTestCase(TestCase):
    def testImport(self):
        import_mei_file(BASE_DIR + "/test_data/390_024.mei")


class NeumeTestCase(TestCase):
    neume = None

    def setUp(self):
        self.neume = Neume()
        self.neume.ulx = 4
        self.neume.uly = 3
        self.neume.lrx = 21
        self.neume.lry = 27

    def test_height(self):
        self.assertEquals(self.neume.get_height(), 24)

    def test_width(self):
        self.assertEquals(self.neume.get_width(), 17)

# class GameraXMLTestCase(TestCase):
#     gamera_file = None
#
#     def setUp(self):
#         gamera_string = open(BASE_DIR + "/test_data/390_020").read()
#         self.gamera_file = GameraXML(gamera_string)
#
#     def test_get_names(self):
#         print self.gamera_file.get_names()
#
#     def tearDown(self):
#         self.gamera_file = None
#
#
# class RunLengthImageTestCase(TestCase):
#     def test_get_location_of_runlength(self):
#         rli = RunLengthImage(3, 3, "5 4")
#         self.assertEquals(rli.get_location_of_runlength(0), (0, 0))
#         self.assertEquals(rli.get_location_of_runlength(1), (1, 0))
#         self.assertEquals(rli.get_location_of_runlength(2), (2, 0))
#         self.assertEquals(rli.get_location_of_runlength(3), (0, 1))
#         self.assertEquals(rli.get_location_of_runlength(4), (1, 1))
#         self.assertEquals(rli.get_location_of_runlength(5), (2, 1))
#         self.assertEquals(rli.get_location_of_runlength(6), (0, 2))
#         self.assertEquals(rli.get_location_of_runlength(7), (1, 2))
#         self.assertEquals(rli.get_location_of_runlength(8), (2, 2))
#
#     def test_get_image(self):
#         rl = "52 4 52 7 50 8 48 11 46 11 46 12 45 12 44 12 45 13 44 13" \
#              " 43 14 44 13 44 11 45 9 48 9 47 10 47 9 48 9 48 9 48 9 48" \
#              " 9 48 8 49 9 48 9 47 8 1 1 47 8 48 9 48 9 48 10 47 10 47 " \
#              "10 47 10 48 10 46 11 46 11 46 11 46 11 46 11 46 11 46 10" \
#              " 47 11 46 11 47 9 48 9 49 9 48 9 49 9 48 6 51 5 53 4 54 " \
#              "3 55 2 56 0 "
#
#         rli = RunLengthImage(58, 52, rl)
#         image = rli.get_image()
#         image.save(MEDIA_ROOT + "test.png")
