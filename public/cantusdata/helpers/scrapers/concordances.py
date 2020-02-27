from html.parser import HTMLParser
import urllib.request
import sys
import re

class ConcordancesScraper(HTMLParser):
    """"Get the list of all concordances in Cantus Database.

    Extracts all the concordances listed in the Cantus Databse website
    by scraping the html code.
    """
    def __init__(self):
        super(ConcordancesScraper, self).__init__()
        self.regexp = (r'^(?P<letter_code>[A-Z])\s\s'
                   r'(?P<institution_city>.*),\s'
                   r'(?P<institution_name>.*),\s'
                   r'(?P<library_manuscript_name>.*)\s\('
                   r'(?P<date>.*), from (?P<location>.*)\)\s\[RISM:\s'
                   r'(?P<rism_code>.*)\]$')
        self.is_concordance = False
        self.concordances = []
        self.flush()

    def flush(self):
        self.concordances = []

    def retrieve_concordances(self):
        ret = self.concordances.copy()
        self.flush()
        return ret

    def handle_starttag(self, tag, attrs):
        if tag == 'tt':
            self.is_concordance = True

    def handle_endtag(self, tag):
        if tag == 'tt' and self.is_concordance:
            self.is_concordance = False

    def handle_data(self, data):
        if self.is_concordance:
            m = re.match(self.regexp, data)
            if m:
                self.concordances.append(m.groupdict())


sources_url = 'http://cantus.uwaterloo.ca/description'
contents = urllib.request.urlopen(sources_url).read().decode('utf-8')
parser = ConcordancesScraper()
parser.feed(contents)
concordances = parser.retrieve_concordances()