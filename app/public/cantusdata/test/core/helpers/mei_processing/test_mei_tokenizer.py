from unittest import TestCase
from os import path
import json
from cantusdata.settings import BASE_DIR
from cantusdata.helpers.mei_processing.mei_tokenizer import (
    MEITokenizer,
    generate_ngrams,
)


TEST_MEI_FILE = path.join(
    BASE_DIR,
    "cantusdata",
    "test",
    "core",
    "helpers",
    "mei_processing",
    "test_mei_files",
    "cdn-hsmu-m2149l4_001r.mei",
)


class MEITokenizerTestCase(TestCase):

    def test_generate_ngrams(self) -> None:
        with self.subTest("Ngrams from 2 to 3"):
            sequence = [1, 2, 3, 4, 5]
            min_ngram = 2
            max_ngram = 3
            ngrams = list(generate_ngrams(sequence, min_ngram, max_ngram))
            self.assertEqual(
                ngrams,
                [[1, 2], [2, 3], [3, 4], [4, 5], [1, 2, 3], [2, 3, 4], [3, 4, 5]],
            )
        with self.subTest("Ngrams from 3 to 5"):
            sequence = [1, 2, 3, 4, 5]
            min_ngram = 3
            max_ngram = 5
            ngrams = list(generate_ngrams(sequence, min_ngram, max_ngram))
            self.assertEqual(
                ngrams,
                [
                    [1, 2, 3],
                    [2, 3, 4],
                    [3, 4, 5],
                    [1, 2, 3, 4],
                    [2, 3, 4, 5],
                    [1, 2, 3, 4, 5],
                ],
            )

    def test_mei_tokenizer(self) -> None:
        tokenizer_1_2 = MEITokenizer(
            TEST_MEI_FILE,
            min_ngram=1,
            max_ngram=2,
        )
        neume_docs_1_2_grams = tokenizer_1_2.get_neume_ngram_docs()
        neume_component_docs_1_2_grams = tokenizer_1_2.get_neume_component_ngram_docs()
        tokenizer_2_3 = MEITokenizer(
            TEST_MEI_FILE,
            min_ngram=2,
            max_ngram=3,
        )
        neume_docs_2_3_grams = tokenizer_2_3.get_neume_ngram_docs()
        neume_component_docs_2_3_grams = tokenizer_2_3.get_neume_component_ngram_docs()
        tokenizer_3_5 = MEITokenizer(
            TEST_MEI_FILE,
            min_ngram=3,
            max_ngram=5,
        )
        neume_docs_3_5_grams = tokenizer_3_5.get_neume_ngram_docs()
        neume_component_docs_3_5_grams = tokenizer_3_5.get_neume_component_ngram_docs()
        with self.subTest("Number of ngrams"):
            # Number of neumes in file: 117
            # => Number of 1- and 2-grams: 117 + 116 = 233
            # => Number of 2- and 3-grams: 116 + 115 = 231
            # => Number of 3-, 4-, and 5-grams: 115 + 114 + 113 = 342
            self.assertEqual(len(neume_docs_1_2_grams), 233)
            self.assertEqual(len(neume_docs_2_3_grams), 231)
            self.assertEqual(len(neume_docs_3_5_grams), 342)
            # Number of neume components in file: 179
            # => Number of 1- and 2-grams: 179 + 178 = 357
            # => Number of 2- and 3-grams: 178 + 177 = 355
            # => Number of 3-, 4-, and 5-grams: 177 + 176 + 175 = 528
            self.assertEqual(len(neume_component_docs_1_2_grams), 357)
            self.assertEqual(len(neume_component_docs_2_3_grams), 355)
            self.assertEqual(len(neume_component_docs_3_5_grams), 528)
        # First three neumes in test file:
        # <neume xml:id="neume-0000001734946468">
        #     <nc xml:id="nc-0000000895518447" facs="#zone-0000001993884372" oct="3" pname="d"/>
        # </neume>
        # <neume xml:id="neume-0000000001979919">
        #     <nc xml:id="nc-0000001973406668" facs="#zone-0000001466045923" oct="3" pname="d"/>
        #     <nc xml:id="nc-0000000472608670" facs="#zone-0000000528011450" oct="3" pname="c"/>
        # </neume>
        # <neume xml:id="m-10023faa-5a94-4eb8-adbf-378d19a7edaa">
        #     <nc xml:id="m-d6735a59-f657-4197-a004-c949253f9268" facs="#m-0306c35f-6624-477a-8f15-f2995401695a" oct="3" pname="f"/>
        # </neume>
        # Relevant zones for first three neumes:
        # <zone xml:id="zone-0000001993884372" ulx="2608" uly="2399" lrx="2678" lry="2448"/>
        # <zone xml:id="zone-0000001466045923" ulx="2725" uly="2396" lrx="2795" lry="2445"/>
        # <zone xml:id="zone-0000000528011450" ulx="2795" uly="2444" lrx="2865" lry="2493"/>
        # <zone xml:id="m-0306c35f-6624-477a-8f15-f2995401695a" ulx="3015" uly="2292" lrx="3085" lry="2341"/>
        with self.subTest("First neume 1-gram"):
            expected_neume_1gram = {
                "ngram_unit": "neume",
                "location": json.dumps(
                    [{"ulx": 2608, "uly": 2399, "width": 70, "height": 49}]
                ),
                "neume_names": "Punctum",
            }
            self.assertEqual(neume_docs_1_2_grams[0], expected_neume_1gram)
        with self.subTest("First neume component 1-gram"):
            expected_first_neume_component_1gram = {
                "ngram_unit": "neume_component",
                "location": json.dumps(
                    [{"ulx": 2608, "uly": 2399, "width": 70, "height": 49}]
                ),
                "pitch_names": "d",
                "intervals": "",
                "contours": "",
            }
            self.assertEqual(
                neume_component_docs_1_2_grams[0],
                expected_first_neume_component_1gram,
            )
        with self.subTest("First neume 3-gram"):
            expected_neume_3gram = {
                "ngram_unit": "neume",
                "location": json.dumps(
                    [{"ulx": 2608, "uly": 2292, "width": 477, "height": 201}]
                ),
                "neume_names": "Punctum_Clivis_Punctum",
            }
            self.assertEqual(neume_docs_3_5_grams[0], expected_neume_3gram)
        with self.subTest("First neume component 3-gram"):
            expected_first_neume_component_3gram = {
                "ngram_unit": "neume_component",
                "location": json.dumps(
                    [{"ulx": 2608, "uly": 2396, "width": 257, "height": 97}]
                ),
                "pitch_names": "d_d_c",
                "intervals": "0_-2",
                "contours": "s_d",
            }
            self.assertEqual(
                neume_component_docs_3_5_grams[0],
                expected_first_neume_component_3gram,
            )
        with self.subTest("Second neume component 3-gram"):
            expected_second_neume_component_3gram = {
                "ngram_unit": "neume_component",
                "location": json.dumps(
                    [{"ulx": 2725, "uly": 2292, "width": 360, "height": 201}]
                ),
                "pitch_names": "d_c_f",
                "intervals": "-2_5",
                "contours": "d_u",
            }
            self.assertEqual(
                neume_component_docs_3_5_grams[1],
                expected_second_neume_component_3gram,
            )
