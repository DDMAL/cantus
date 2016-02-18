"""
Processing for the St Gallen MEI format
"""

import uuid
import string

from .abstract_mei_converter import AbstractMEIConverter
from .mei_tokens import NeumeToken
from .location_utils import getLocation


class StGallenMEIConverter (AbstractMEIConverter):
    def process(self):
        neumes = list(NeumeToken.get_all_from_doc(self.doc))

        neume_count = len(neumes)

        for i in range(self.min_gram, self.max_gram + 1):
            for j in range(0, neume_count - i):
                seq = neumes[j:j + i]
                location = getLocation(seq)

                # get neumes without punctuation
                # FIXME(wabain): Why do we want that?
                n_gram_neumes = '_'.join(neume.name for neume in seq)\
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
