from html.parser import HTMLParser

import urllib.request
from pprint import pprint
import sys


class CantusHTML(HTMLParser):
    """ "Get the basic genre metadata from the Cantus Database.

    Notes
    -----
    If you know a better way of doing this, please replace this code.
    It is not ideal but we had no success using the Cantus Web API.
    """

    def __init__(self):
        super(CantusHTML, self).__init__()
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
                    self.dictionary[self.key] = self.value
                    self.key = ""
                    self.value = ""

    def handle_data(self, data):
        if self.is_field_name:
            if not data.isspace():
                self.key = data
        if self.is_field_description:
            if not data.isspace():
                self.value = data


if __name__ == "__main__":
    genre_url = "http://cantus.uwaterloo.ca/genre"
    contents = urllib.request.urlopen(genre_url).read().decode("utf-8")
    parser = CantusHTML()
    parser.feed(contents)
    genres = parser.retrieve_genres()
    for genre, description in genres.items():
        print(genre, description)