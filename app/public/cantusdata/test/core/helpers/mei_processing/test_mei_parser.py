from unittest import TestCase
from os import path
from cantusdata.settings import BASE_DIR
from cantusdata.helpers.mei_processing.mei_parser import (
    MEIParser,
    get_contour_from_interval,
    get_interval_between_neume_components,
    analyze_neume,
)


class MEIParserTestCase(TestCase):
    default_bounding_box = {"coordinates": (-1, -1, -1, -1), "rotate": 0.0}
    neume_component_g3 = {
        "pname": "g",
        "octave": 3,
        "bounding_box": default_bounding_box,
    }
    neume_component_d4 = {
        "pname": "d",
        "octave": 4,
        "bounding_box": default_bounding_box,
    }
    neume_component_d3 = {
        "pname": "d",
        "octave": 3,
        "bounding_box": default_bounding_box,
    }
    neume_component_b2 = {
        "pname": "b",
        "octave": 2,
        "bounding_box": default_bounding_box,
    }

    def test_mei_parser(self):
        parser = MEIParser(
            path.join(
                BASE_DIR,
                "cantusdata",
                "test",
                "core",
                "helpers",
                "mei_processing",
                "test_mei_files",
                "cdn-hsmu-m2149l4_001r.mei",
            )
        )
        zones = parser.zones
        syllables = parser.syllables
        self.assertEqual(len(zones), 324)
        self.assertEqual(len(syllables), 116)

    def test_get_contour_from_interval(self):
        self.assertEqual(get_contour_from_interval(0), "s")
        self.assertEqual(get_contour_from_interval(1), "u")
        self.assertEqual(get_contour_from_interval(-3), "d")

    def test_get_interval_between_neume_components(self):
        self.assertEqual(
            get_interval_between_neume_components(
                self.neume_component_g3, self.neume_component_d4
            ),
            7,
        )
        self.assertEqual(
            get_interval_between_neume_components(
                self.neume_component_d4, self.neume_component_g3
            ),
            -7,
        )
        self.assertEqual(
            get_interval_between_neume_components(
                self.neume_component_g3, self.neume_component_d3
            ),
            -5,
        )
        self.assertEqual(
            get_interval_between_neume_components(
                self.neume_component_g3, self.neume_component_b2
            ),
            -8,
        )

    def test_analyze_neume(self):
        neume_components_1 = [self.neume_component_d3, self.neume_component_g3]
        neume_components_2 = [
            self.neume_component_d3,
            self.neume_component_g3,
            self.neume_component_d3,
        ]
        neume_components_3 = [self.neume_component_d4, self.neume_component_g3]
        neume_components_4 = [
            self.neume_component_b2,
            self.neume_component_b2,
            self.neume_component_b2,
        ]
        neume_components_5 = [self.neume_component_d4]
        self.assertEqual(analyze_neume(neume_components_1), ("Pes", [5], ["u"]))
        self.assertEqual(
            analyze_neume(neume_components_2), ("Torculus", [5, -5], ["u", "d"])
        )
        self.assertEqual(analyze_neume(neume_components_3), ("Clivis", [-7], ["d"]))
        self.assertEqual(
            analyze_neume(neume_components_4), ("Tristopha", [0, 0], ["s", "s"])
        )
        self.assertEqual(analyze_neume(neume_components_5), ("Punctum", [], []))
