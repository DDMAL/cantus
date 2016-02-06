import uuid
import string

from .abstract_mei_converter import AbstractMEIConverter, getNeumeNames
from .location_utils import getLocation, LookupCache


class StGallenMEIConverter (AbstractMEIConverter):
    """
    An MEI convereter which works with the St Gallen MEI format
    """

    def getNgramDocuments(self, mei_doc, page_number):
        cache = LookupCache(mei_doc)

        neumes = mei_doc.getElementsByName('neume')

        n_neumes = len(neumes)  # number of notes in file
        print("n_neumes: {0}, shortest_gram: {1}, longest_gram: {2}".format(
                n_neumes, self.min_gram, self.max_gram))

        mydocs = []

        for i in range(self.min_gram, self.max_gram + 1):
            print "Processing pitch sequences..."
            for j in range(0, n_neumes - i):
                seq = neumes[j:j + i]
                location = getLocation(seq, cache)

                # get neumes without punctuation
                # FIXME(wabain): Why do we want that?
                n_gram_neumes = getNeumeNames(seq)\
                    .lower()\
                    .replace('_', ' ')\
                    .translate(string.maketrans("", ""), string.punctuation)\
                    .replace(' ', '_')

                new_doc = {
                    'id': str(uuid.uuid4()),
                    'type': self.TYPE,
                    'siglum_slug': self.siglum_slug,
                    'folio': page_number,
                    'neumes': n_gram_neumes,
                    'location': str(location)
                }

                mydocs.append(new_doc)

        return mydocs
