from unittest import TestCase
from os import path
from cantusdata.settings import BASE_DIR
from cantusdata.helpers.mei_processing.mei_parser import (
    MEIParser,
    get_contour_from_interval,
    get_interval_between_neume_components,
    analyze_neume,
)
from cantusdata.helpers.mei_processing.mei_parsing_types import (
    NeumeComponentElementData,
    Zone,
)


class MEIParserTestCase(TestCase):
    default_bounding_box: Zone = {"coordinates": (-1, -1, -1, -1), "rotate": 0.0}
    nc_elem_g3: NeumeComponentElementData = {
        "pname": "g",
        "octave": 3,
        "bounding_box": default_bounding_box,
    }
    nc_elem_d4: NeumeComponentElementData = {
        "pname": "d",
        "octave": 4,
        "bounding_box": default_bounding_box,
    }
    nc_elem_d3: NeumeComponentElementData = {
        "pname": "d",
        "octave": 3,
        "bounding_box": default_bounding_box,
    }
    nc_elem_b2: NeumeComponentElementData = {
        "pname": "b",
        "octave": 2,
        "bounding_box": default_bounding_box,
    }

    def test_mei_parser(self) -> None:
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
        with self.subTest("Test number of zones"):
            self.assertEqual(len(zones), 324)
        with self.subTest("Test number of syllables"):
            self.assertEqual(len(syllables), 116)
        with self.subTest("Test sample zone #1"):
            zone_key = "#m-bd6dbd3e-46ec-4244-bfb9-b22aae69116d"
            expected_zone = {
                "coordinates": (1191, 4482, 5276, 4791),
                "rotate": -0.180727,
            }
            self.assertIn(zone_key, zones)
            self.assertEqual(zones[zone_key], expected_zone)
        with self.subTest("Test sample zone #2"):
            zone_key = "#zone-0000001876581719"
            expected_zone = {
                "coordinates": (4933, 7834, 5265, 8034),
                "rotate": 0.0,
            }
            self.assertIn(zone_key, zones)
            self.assertEqual(zones[zone_key], expected_zone)
        with self.subTest("Test first syllable"):
            # First and second syllables:
            ## <syllable xml:id="syllable-0000001795831030">
            ##     <syl xml:id="syl-0000000707236922" facs="#zone-0000001663913937">Ec</syl>
            ##     <neume xml:id="neume-0000001734946468">
            ##         <nc xml:id="nc-0000000895518447" facs="#zone-0000001993884372" oct="3" pname="d"/>
            ##     </neume>
            ## </syllable>
            ## <syllable xml:id="syllable-0000001438713822">
            ##     <syl xml:id="syl-0000000470772630" facs="#zone-0000001748077003">ce</syl>
            ##     <neume xml:id="neume-0000000001979919">
            ##         <nc xml:id="nc-0000001973406668" facs="#zone-0000001466045923" oct="3" pname="d"/>
            ##         <nc xml:id="nc-0000000472608670" facs="#zone-0000000528011450" oct="3" pname="c"/>
            ##     </neume>
            ## </syllable>
            # Relevant zones (for first syllable and the single neume component in that syllable):
            ## <zone xml:id="zone-0000001663913937" ulx="2426" uly="2451" lrx="2639" lry="2651"/>
            ## <zone xml:id="zone-0000001993884372" ulx="2608" uly="2399" lrx="2678" lry="2448"/>
            expected_first_syllable = {
                "text": {
                    "text": "Ec",
                    "bounding_box": {
                        "coordinates": (2426, 2451, 2639, 2651),
                        "rotate": 0.0,
                    },
                },
                "neumes": [
                    {
                        "neume_type": "Punctum",
                        "neume_components": [
                            {
                                "pname": "d",
                                "octave": 3,
                                "bounding_box": {
                                    "coordinates": (2608, 2399, 2678, 2448),
                                    "rotate": 0.0,
                                },
                                "interval": 0,
                                "contour": "s",
                            }
                        ],
                        "bounding_box": {
                            "coordinates": (2608, 2399, 2678, 2448),
                            "rotate": 0.0,
                        },
                        "system": 1,
                    }
                ],
            }
            self.assertEqual(syllables[0], expected_first_syllable)
        with self.subTest("Test last syllable"):
            # Last syllable:
            ## <syllable xml:id="syllable-0000001099935725">
            ##     <syl xml:id="syl-0000001384779917" facs="#zone-0000001876581719">gil</syl>
            ##     <neume xml:id="neume-0000001160139058">
            ##         <nc xml:id="nc-0000000858715089" facs="#zone-0000001183492561" oct="2" pname="e"/>
            ##         <nc xml:id="nc-0000001382334633" facs="#zone-0000002089367816" oct="2" pname="d" tilt="n"/>
            ##     </neume>
            ## </syllable>
            # Relevant zones (for last syllable and the two neume components in that syllable):
            ## <zone xml:id="zone-0000001876581719" ulx="4933" uly="7834" lrx="5265" lry="8034"/>
            ## <zone xml:id="zone-0000001183492561" ulx="5037" uly="7724" lrx="5108" lry="7774"/>
            ## <zone xml:id="zone-0000002089367816" ulx="5104" uly="7774" lrx="5175" lry="7824"/>
            expected_last_syllable = {
                "text": {
                    "text": "gil",
                    "bounding_box": {
                        "coordinates": (4933, 7834, 5265, 8034),
                        "rotate": 0.0,
                    },
                },
                "neumes": [
                    {
                        "neume_type": "Clivis",
                        "neume_components": [
                            {
                                "pname": "e",
                                "octave": 2,
                                "bounding_box": {
                                    "coordinates": (5037, 7724, 5108, 7774),
                                    "rotate": 0.0,
                                },
                                "interval": -2,
                                "contour": "d",
                            },
                            {
                                "pname": "d",
                                "octave": 2,
                                "bounding_box": {
                                    "coordinates": (5104, 7774, 5175, 7824),
                                    "rotate": 0.0,
                                },
                                "interval": None,
                                "contour": None,
                            },
                        ],
                        "bounding_box": {
                            "coordinates": (5037, 7724, 5175, 7824),
                            "rotate": 0.0,
                        },
                        "system": 10,
                    }
                ],
            }
            self.assertEqual(syllables[-1], expected_last_syllable)

    def test_get_contour_from_interval(self) -> None:
        self.assertEqual(get_contour_from_interval(0), "s")
        self.assertEqual(get_contour_from_interval(1), "u")
        self.assertEqual(get_contour_from_interval(-3), "d")

    def test_get_interval_between_neume_components(self) -> None:
        with self.subTest("Interval test: ascending P5"):
            self.assertEqual(
                get_interval_between_neume_components(self.nc_elem_g3, self.nc_elem_d4),
                7,
            )
        with self.subTest("Interval test: descending P5"):
            self.assertEqual(
                get_interval_between_neume_components(self.nc_elem_d4, self.nc_elem_g3),
                -7,
            )
        with self.subTest("Interval test: descending P4"):
            self.assertEqual(
                get_interval_between_neume_components(self.nc_elem_g3, self.nc_elem_d3),
                -5,
            )
        with self.subTest("Interval test: descending m6"):
            self.assertEqual(
                get_interval_between_neume_components(self.nc_elem_g3, self.nc_elem_b2),
                -8,
            )

    def test_analyze_neume(self) -> None:
        neume_components_1 = [self.nc_elem_d3, self.nc_elem_g3]
        neume_components_2 = [
            self.nc_elem_d3,
            self.nc_elem_g3,
            self.nc_elem_d3,
        ]
        neume_components_3 = [self.nc_elem_d4, self.nc_elem_g3]
        neume_components_4 = [
            self.nc_elem_b2,
            self.nc_elem_b2,
            self.nc_elem_b2,
        ]
        neume_components_5 = [self.nc_elem_d4]
        with self.subTest("Analyze Pes"):
            self.assertEqual(analyze_neume(neume_components_1), ("Pes", [5], ["u"]))
        with self.subTest("Analyze Torculus"):
            self.assertEqual(
                analyze_neume(neume_components_2), ("Torculus", [5, -5], ["u", "d"])
            )
        with self.subTest("Analyze Clivis"):
            self.assertEqual(analyze_neume(neume_components_3), ("Clivis", [-7], ["d"]))
        with self.subTest("Analyze Tristropha"):
            self.assertEqual(
                analyze_neume(neume_components_4), ("Tristopha", [0, 0], ["s", "s"])
            )
        with self.subTest("Analyze Punctum"):
            self.assertEqual(analyze_neume(neume_components_5), ("Punctum", [], []))
