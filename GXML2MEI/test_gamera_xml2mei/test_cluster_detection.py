"""Run some higher-level tests on the cluster detection algorithm. These cases frankly aren't that
great, but they could catch some serious regressions.
"""

import unittest
import os
import shutil

from gameraXML2MEI import GameraXMLConverter


class ClusterDetectionTest (unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up the resource paths
        cls.basePath = os.path.dirname(__file__)
        cls.outPath = os.path.join(cls.basePath, 'temp')

        if os.path.exists(cls.outPath):
            shutil.rmtree(cls.outPath)

        os.mkdir(cls.outPath)

    @classmethod
    def tearDownClass(cls):
        # Remove the test output directory
        if os.path.exists(cls.outPath):
            shutil.rmtree(cls.outPath)

    def testStGallClustering(self):
        """Test a page from the Sankt Gallen 390 manuscript"""
        self.assertConversionGives('stgall_390_020.xml', initialClusters=16, clusters=16, zones=277)

    def testClusterConsolidation(self):
        """Test a fake file designed to hit some corner cases in the cluster detection

        On the first pass, two clusters will be created, but they should be consolidated into one."""
        self.assertConversionGives('awkward_cluster.xml', initialClusters=2, clusters=1, zones=3)

    def assertConversionGives(self, filename, **info):
        converter = self.getConverter(filename)
        converter.processGamera()
        self.assertDictContainsSubset(info, converter.conversionInfo)

    def getConverter(self, filename):
        infile = os.path.join(self.basePath, 'resources', filename)
        outfile = os.path.join(self.outPath, os.path.splitext(filename)[0] + '.mei')
        return GameraXMLConverter(infile, outfile, {})
