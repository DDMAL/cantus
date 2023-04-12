from html.parser import HTMLParser
import urllib.request
import sys
import re

# April 2023: In order to harmonize the process of importing concordances
# with that of other static data (ie. iiif manifests), concordances are now
# stored in data_dumps/concordances.csv and loaded directly in the
# import_concordance_data function in the import_data command.
# This file is retained for reference.

"""The CAO concordances used to be scraped from the Cantus Website.

However, as of July 2020, this information is no longer on the website.

Now the fields are hardcoded based on the old information of the Website.

Scraper left for reference at the end of the file."""

cao_concordances = """
C  Paris, Bibliothèque nationale de France, lat. 17436 (ninth century, from Compiègne) [RISM: F-Pn lat. 17436]
G  Durham, Cathedral Library, B. III. 11 (eleventh century, from northern France) [RISM: GB-DRc B. III. 11]
B  Bamberg, Staatsbibliothek, lit. 23 (eleventh or twelfth century, from Bamberg) [RISM: D-BAs lit. 23]
E  Ivrea, Biblioteca Capitolare, 106 (eleventh century, from Ivrea) [RISM: I-IV 106]
M  Monza, Basilica di S. Giovanni Battista - Biblioteca Capitolare e Tesoro, C. 12/75 (eleventh century, from Monza) [RISM: I-MZ C. 12/75]
V  Verona, Biblioteca Capitolare, XCVIII (eleventh century, from Verona) [RISM: I-VEcap XCVIII]
H  Sankt Gallen, Stiftsbibliothek, 390-391 (“Hartker antiphoner,” early eleventh century, from St. Gall) [RISM: CH-SGs 390-391]
R  Zürich, Zentralbibliothek, Rh. 28 (thirteenth century, from Rheinau) [RISM: CH-Zz Rh. 28]
D  Paris, Bibliothèque nationale de France, lat. 17296 (twelfth century, from St. Denis) [RISM: F-Pn lat. 17296]
F  Paris, Bibliothèque nationale de France, lat. 12584 (twelfth century, from St. Maur-les-Fossés) [RISM: F-Pn lat. 12584]
S  London, The British Library, add. 30850 (eleventh century, from Silos) [RISM: GB-Lbl add. 30850]
L  Benevento, Biblioteca Capitolare, V 21 (late twelfth century, from San Lupo) [RISM: I-BV V. 21]
"""

regexp = re.compile(
    (
        r"^(?P<letter_code>[A-Z])\s\s"
        r"(?P<institution_city>.*),\s"
        r"(?P<institution_name>.*),\s"
        r"(?P<library_manuscript_name>.*)\s\("
        r"(?P<date>.*), from (?P<location>.*)\)\s\[RISM:\s"
        r"(?P<rism_code>.*)\]$"
    )
)

concordances = []
for line in cao_concordances.split("\n"):
    m = regexp.match(line)
    if m:
        concordances.append(m.groupdict())


# class ConcordancesScraper(HTMLParser):
#     """"Get the list of all concordances in Cantus Database.
#
#     Extracts all the concordances listed in the Cantus Databse website
#     by scraping the html code.
#     """
#     def __init__(self):
#         super(ConcordancesScraper, self).__init__()
#         self.regexp = re.compile(
#             (r'^(?P<letter_code>[A-Z])\s\s'
#             r'(?P<institution_city>.*),\s'
#             r'(?P<institution_name>.*),\s'
#             r'(?P<library_manuscript_name>.*)\s\('
#             r'(?P<date>.*), from (?P<location>.*)\)\s\[RISM:\s'
#             r'(?P<rism_code>.*)\]$')
#         )
#         self.is_concordance = False
#         self.concordances = []
#         self.flush()
#
#     def flush(self):
#         self.concordances = []
#
#     def retrieve_concordances(self):
#         ret = self.concordances.copy()
#         self.flush()
#         return ret
#
#     def handle_starttag(self, tag, attrs):
#         if tag == 'tt':
#             self.is_concordance = True
#
#     def handle_endtag(self, tag):
#         if tag == 'tt' and self.is_concordance:
#             self.is_concordance = False
#
#     def handle_data(self, data):
#         if self.is_concordance:
#             m = self.regexp.match(data)
#             if m:
#                 self.concordances.append(m.groupdict())
#
# sources_url = 'http://cantus.uwaterloo.ca/description'
# contents = urllib.request.urlopen(sources_url).read().decode('utf-8')
# parser = ConcordancesScraper()
# parser.feed(contents)
# concordances = parser.retrieve_concordances()
