from cantusdata.helpers.mei_conversion.mei_parse import parse
from unittest import TestCase
from os import path
from cantusdata.settings import BASE_DIR

class IIIFTestCase(TestCase):
    def test_salzinnes(self):
        with open(path.join(BASE_DIR, "cantusdata", "test", "core", "helpers", "mei_conversion", "salzinnes_001r.ground"), "r") as sal:
            ground = sal.read().strip()
        neumes, global_sequences = parse(path.join(BASE_DIR, "cantusdata", "test", "core", "helpers", "mei_conversion", "salzinnes_001r.mei"))
        pitches = "".join(global_sequences["pitches"])
        assert(ground == pitches)