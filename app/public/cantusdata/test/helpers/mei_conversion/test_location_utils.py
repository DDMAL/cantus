from django.test import TestCase

from cantusdata.helpers.mei_conversion.mei_tokens import NeumeToken
from cantusdata.helpers.mei_conversion.location_utils import getLocation


class GetLocationTestCase (TestCase):
    SYSTEM_1_NEUMES = [
        NeumeToken('a', 'clivis', 'sys-1', {'ulx': 10, 'uly': 20, 'lrx': 50, 'lry': 60}),
        NeumeToken('b', 'punctum', 'sys-1', {'ulx': 60, 'uly': 10, 'lrx': 75, 'lry': 50}),
    ]

    SYSTEM_1_LOCATION = {
        'ulx': 10,
        'uly': 10,
        'width': 65,
        'height': 50
    }

    SYSTEM_2_NEUMES = [
        NeumeToken('c', 'clivis', 'sys-2', {'ulx': 110, 'uly': 120, 'lrx': 150, 'lry': 160}),
        NeumeToken('d', 'punctum', 'sys-2', {'ulx': 160, 'uly': 110, 'lrx': 175, 'lry': 150}),
    ]

    SYSTEM_2_LOCATION = {
        'ulx': 110,
        'uly': 110,
        'width': 65,
        'height': 50
    }

    SYSTEM_3_NEUMES = [
        NeumeToken('e', 'clivis', 'sys-3', {'ulx': 210, 'uly': 220, 'lrx': 250, 'lry': 260}),
        NeumeToken('f', 'punctum', 'sys-3', {'ulx': 260, 'uly': 210, 'lrx': 275, 'lry': 250}),
    ]

    SYSTEM_3_LOCATION = {
        'ulx': 210,
        'uly': 210,
        'width': 65,
        'height': 50
    }

    def testSingleSystemLocation(self):
        self.assertListEqual(getLocation(self.SYSTEM_1_NEUMES), [self.SYSTEM_1_LOCATION])

    def testMultipleSystemLocation(self):
        neumes = self.SYSTEM_1_NEUMES + self.SYSTEM_2_NEUMES + self.SYSTEM_3_NEUMES
        expected = [self.SYSTEM_1_LOCATION, self.SYSTEM_2_LOCATION, self.SYSTEM_3_LOCATION]

        self.assertListEqual(getLocation(neumes), expected)
