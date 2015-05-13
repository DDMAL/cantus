import unittest

from gameraXML2MEI import Zone, ZoneCluster, overlaps


class ZoneClusteringTest (unittest.TestCase):
    def setUp(self):
        self.zones = [
            Zone('1', 0,  0,  10, 5), # <-- no overlap with zone 2
            Zone('3', 10, 10, 20, 25), # <-- overlaps with zone 3
            Zone('3', 20, 20, 30, 30), # <-- no overlap with zone 4
            Zone('4', 30, 35, 40, 40)
        ]

    def testPartialRegionOverlap(self):
        """Test support for cases where regions overlap partially

        Neither region is fully contained within the other.
        """
        region1 = ZoneCluster(self.zones[:2])
        region2 = ZoneCluster(self.zones[2:])
        self.assertTrue(overlaps(region1, region2))
        self.assertTrue(overlaps(region2, region1))

    def testRegionCompleteContainment(self):
        """Test support for cases where regions overlap completely

        One region is completely contained within the other
        """
        region1 = ZoneCluster(self.zones[:2])
        region1.addZone(self.zones[3])

        region2 = ZoneCluster([self.zones[2]])

        self.assertTrue(overlaps(region1, region2))
        self.assertTrue(overlaps(region2, region1))

    def testRegionWithTolerance(self):
        """Test support for tolerance thresholds"""
        region1 = ZoneCluster([self.zones[0]])
        region2 = ZoneCluster([self.zones[1]])

        self.assertFalse(overlaps(region1, region2))
        self.assertFalse(overlaps(region2, region1))

        self.assertTrue(overlaps(region1, region2, 10))
        self.assertTrue(overlaps(region2, region1, 10))

        # What if the region falls entirely within the space between the
        # external edge of the other region and the tolerance threshold?
        # This shouldn't really be a corner case, but let's check.
        region3 = ZoneCluster([self.zones[2]])
        region4 = ZoneCluster([self.zones[3]])

        self.assertFalse(overlaps(region3, region4))
        self.assertFalse(overlaps(region4, region3))

        self.assertTrue(overlaps(region3, region4, 15))
        self.assertTrue(overlaps(region4, region3, 15))
