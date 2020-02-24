from html.parser import HTMLParser
import urllib.request
import sys

class SourcesScraper(HTMLParser):
    """"Get the list of all sources in Cantus Database.

    Extracts all the sources listed in the Cantus Databse website
    by scraping the html code.
    """
    def __init__(self):
        super(SourcesScraper, self).__init__()
        self.flush()

    def flush(self):
        self.dictionary = {}

    def retrieve_sources(self):
        ret = self.dictionary.copy()
        self.flush()
        return ret

    def handle_starttag(self, tag, attrs):
        if tag == 'a' and len(attrs) == 2:
            attr1, link = attrs[0]
            attr2, title = attrs[1]
            if attr1 == 'href' and attr2 == 'title' and link.startswith('/source/'):
                self.dictionary[link] = title

sources_url = 'http://cantus.uwaterloo.ca/sources'
contents = urllib.request.urlopen(sources_url).read().decode('utf-8')
parser = SourcesScraper()
parser.feed(contents)
sources = parser.retrieve_sources()