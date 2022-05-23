import os
import json

from solr import SolrConnection

from django.conf import settings

from rest_framework.test import APITestCase
from rest_framework import status

from cantusdata.helpers.mei_conversion import MEIConverter
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript


RESOURCE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../test_data'))
MEI_FIXTURE = os.path.join(RESOURCE_DIR, 'salz_001r.mei')
MEI_FIXTURE_FOLIO = '001r'
MEI_FIXTURE_SIGLUM = 'cdn-hsmu-m2149l4'
MEI_FIXTURE_ID = 133
MEI_FIXTURE_URI = 'http://image.com/image.jp2'


class SearchNotationTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        # First, add a folio to Solr so that the image_uri can be retrieved during the MEI conversion
        # Using curl here because it turned out to be easier than solrconn.add and gives better error messages
        os.system("curl {0}/update/?commit=true -H 'Content-Type: text/xml' -d '<add><doc>\
        <field name=\"id\">testid</field>\
        <field name=\"type\">cantusdata_folio</field>\
        <field name=\"manuscript_id\">{1}</field>\
        <field name=\"number\">{2}</field>\
        <field name=\"image_uri\">{3}</field>\
        </doc></add>'".format(settings.SOLR_SERVER, MEI_FIXTURE_ID, MEI_FIXTURE_FOLIO, MEI_FIXTURE_URI))

        docs = list(MEIConverter.process_file(MEI_FIXTURE, MEI_FIXTURE_SIGLUM, MEI_FIXTURE_ID))

        # Sanity check
        solrconn = SolrConnection(settings.SOLR_SERVER)
        prequery = solrconn.query('type:cantusdata_music_notation AND manuscript:' + MEI_FIXTURE_SIGLUM)
        assert prequery.numFound == 0, 'MEI was already in the database when loading the test fixture'

        solrconn.add_many(docs)
        solrconn.commit()

    @classmethod
    def tearDownClass(cls):
        solrconn = SolrConnection(settings.SOLR_SERVER)
        solrconn.delete_query('type:cantusdata_music_notation AND manuscript:' + MEI_FIXTURE_SIGLUM)
        solrconn.delete_query('type:cantusdata_folio AND manuscript_id:{0}'.format(MEI_FIXTURE_ID))
        solrconn.commit()

    def test_get_pnames(self):
        response = self.client.get("/notation-search/", {
            "q": "edffgffc",
            "type": "pnames",
            "manuscript": MEI_FIXTURE_SIGLUM
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, {
            "numFound": 1,
            "results": [
                {
                    "semitones": [-2, 3, 0, 2, -2, 0, 7],
                    "pnames": ["e", "d", "f", "f", "g", "f", "f", "c"],
                    "neumes": ["clivis", "punctum", "punctum", "punctum", "punctum", "punctum", "punctum"],
                    "boxes": [{"y": 3252, "p": MEI_FIXTURE_URI, "f": MEI_FIXTURE_FOLIO, "x": 1262, "w": 498, "h": 231}],
                    "intervals": ["d2", "u3", "r", "u2", "d2", "r", "u5"],
                    "contour": ["d", "u", "r", "u", "d", "r", "u"]
                }
            ]
        })

    def test_get_neumes(self):
        response = self.client.get("/notation-search/", {
            "q": "torculus punctum punctum clivis",
            "type": "neumes",
            "manuscript": MEI_FIXTURE_SIGLUM
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, json.dumps({
            "numFound": 1,
            "results": [
                {
                    "semitones": [2, -2, -8, 7, -2, -2],
                    "pnames": ["f", "g", "f", "a", "e", "d", "c"],
                    "neumes": ["torculus", "punctum", "punctum", "clivis"],
                    "boxes": [
                        {"y": 1378, "p": MEI_FIXTURE_URI, "f": MEI_FIXTURE_FOLIO, "x": 3109, "w": 119, "h": 96},
                        {"y": 1811, "p": MEI_FIXTURE_URI, "f": MEI_FIXTURE_FOLIO, "x": 1537, "w": 304, "h": 163}
                    ],
                    "intervals": ["u2", "d2", "d6", "u5", "d2", "d2"],
                    "contour": ["u", "d", "d", "u", "d", "d"]
                }
            ]
        }))
