"""
Processing for the St Gallen MEI format
"""

import uuid
import string

from .abstract_mei_converter import AbstractMEIConverter, getNeumeNames
from .location_utils import getLocation


class StGallenMEIConverter (AbstractMEIConverter):
    def process(self):
        neumes = self.doc.getElementsByName('neume')

        neume_count = len(neumes)

        print("n_neumes: {0}, shortest_gram: {1}, longest_gram: {2}".format(
                neume_count, self.min_gram, self.max_gram))

        for i in range(self.min_gram, self.max_gram + 1):
            print "Processing pitch sequences..."
            for j in range(0, neume_count - i):
                seq = neumes[j:j + i]
                location = getLocation(seq, self.cache)

                # get neumes without punctuation
                # FIXME(wabain): Why do we want that?
                n_gram_neumes = getNeumeNames(seq)\
                    .lower()\
                    .replace('_', ' ')\
                    .translate(string.maketrans("", ""), string.punctuation)\
                    .replace(' ', '_')

                yield {
                    'id': str(uuid.uuid4()),
                    'type': self.TYPE,
                    'siglum_slug': self.siglum_slug,
                    'folio': self.page_number,
                    'neumes': n_gram_neumes,
                    'location': str(location)
                }
