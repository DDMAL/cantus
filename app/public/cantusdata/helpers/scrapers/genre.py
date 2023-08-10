from html.parser import HTMLParser
import urllib.request
import sys


class GenreScraper(HTMLParser):
    """Get the genres and description from the Cantus Database.

    Notes
    -----
    If you know a better way of doing this, please replace this code.
    It is not ideal but I had no success using the Cantus Web API (napulen).
    """

    def __init__(self):
        super(GenreScraper, self).__init__()
        self.flush()

    def flush(self):
        self.is_field_name = False
        self.is_field_description = False
        self.key = ""
        self.value = ""
        self.dictionary = {}

    def retrieve_genres(self):
        ret = self.dictionary.copy()
        self.flush()
        return ret

    def handle_starttag(self, tag, attrs):
        field_name = ("class", "views-field views-field-name")
        field_description = ("class", "views-field views-field-description")
        if tag == "td":
            if field_name in attrs:
                self.is_field_name = True
            elif field_description in attrs:
                self.is_field_description = True

    def handle_endtag(self, tag):
        if tag == "td":
            if self.is_field_name:
                self.is_field_name = False
            if self.is_field_description:
                self.is_field_description = False
                if self.key and self.value:
                    self.dictionary[self.key.strip("[]")] = self.value
                    self.key = ""
                    self.value = ""

    def handle_data(self, data):
        if self.is_field_name:
            if not data.isspace():
                self.key = data
        if self.is_field_description:
            if not data.isspace():
                self.value = data


genre_url = "https://cantusdatabase.org/genres"
contents = urllib.request.urlopen(genre_url).read().decode("utf-8")
parser = GenreScraper()
parser.feed(contents)
genres = parser.retrieve_genres()
