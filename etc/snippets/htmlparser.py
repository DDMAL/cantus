from html.parser import HTMLParser

import urllib.request
from pprint import pprint
import sys


class CantusHTML(HTMLParser):
    """ "Get the basic manuscript metadata from the Cantus Database.

    Users provide a link to the manuscript in the cantus database,
    this class is used to scrape the content of the html and get the
    basic information about the manuscript.

    Notes
    -----
    If you know a better way of doing this, please replace this code.
    It is not ideal but we had no success using the Cantus Web API.
    """

    def __init__(self):
        super(CantusHTML, self).__init__()
        self.flush()
        self.view_content_keys = [
            "Provenance",
            "Date",
            "Cursus",
            "Indexed by",
            "Proofreader/s",
            "Contributor",
        ]

    def flush(self):
        self.is_field_label = False
        self.is_field_item = False
        # Getting the right hand of the website is more difficult.
        # There is no clear structure. Getting all the text
        # within the "view-content" class div seems the best option.
        self.view_content_div = 0
        self.key = ""
        self.value = ""
        self.unparsed_view_content = []
        self.dictionary = {}

    def parse_view_content(self):
        key = ""
        value = []
        for entry in self.unparsed_view_content:
            possible_key = entry.split(":")[0].strip()
            if possible_key in self.view_content_keys:
                if key and value:
                    self.dictionary[key] = value
                key = possible_key
                value = []
            else:
                value.append(entry)

    def format_view_content(self):
        for key in self.view_content_keys:
            if key in self.dictionary:
                string_values = self.dictionary[key]
                final_string = ""
                if key == "Indexed by":
                    pairs = []
                    for name, affiliation in zip(
                        string_values[::2], string_values[1::2]
                    ):
                        pairs.append("{}, {}.".format(name, affiliation))
                    final_string = " ".join(pairs)
                elif key == "Proofreader/s":
                    final_string = ". ".join(string_values)
                else:
                    final_string = "".join(string_values)
                self.dictionary[key] = final_string

    def retrieve_metadata(self):
        ret = self.dictionary.copy()
        self.flush()
        return ret

    def handle_starttag(self, tag, attrs):
        field_label = ("class", "field-label")
        field_item = ("class", "field-item even")
        view_content = ("class", "view-content")
        if tag == "div":
            if view_content in attrs or self.view_content_div > 0:
                self.view_content_div += 1
            elif field_label in attrs:
                self.is_field_label = True
            elif field_item in attrs:
                self.is_field_item = True

    def handle_endtag(self, tag):
        if tag == "div":
            if self.is_field_label:
                self.is_field_label = False
            if self.is_field_item:
                if self.key and self.value:
                    self.key = self.key.split(":")[0]
                    self.value = " ".join(self.value.split())
                    self.dictionary[self.key] = self.value
                    self.key = ""
                    self.value = ""
                self.is_field_item = False
            if self.view_content_div > 0:
                if self.view_content_div == 1:
                    # This gets all the text within the
                    # "view-content" tag in the corresponding
                    # entry of the output dictionary
                    self.parse_view_content()
                    # This formats the final string representation
                    # of those "view-content" key,value pairs
                    self.format_view_content()
                    # self.view_content_div = 0
                self.view_content_div -= 1

    def handle_data(self, data):
        if self.is_field_label:
            self.key = data
        if self.is_field_item:
            # descriptions and other sections have embedded
            # html tagsthat require several passes through the
            # handle_data() function hence the '+=' to concatenate
            # all the content spread within several html tags
            self.value += data
        if self.view_content_div > 0:
            # A lot of empty data between divs. Filtering that out.
            if not data.isspace():
                self.unparsed_view_content.append(data)


class CantusAllSourcesHTML(HTMLParser):
    """ "Get the list of all sources in Cantus Database.

    This class is intended mostly for testing (although it
    could be useful in production at some point), it extracts
    all the sources listed in the Cantus Databse website.
    """

    def __init__(self):
        super(CantusAllSourcesHTML, self).__init__()
        self.flush()

    def flush(self):
        self.dictionary = {}

    def retrieve_sources(self):
        ret = self.dictionary.copy()
        self.flush()
        return ret

    def handle_starttag(self, tag, attrs):
        if tag == "a" and len(attrs) == 2:
            attr1, link = attrs[0]
            attr2, title = attrs[1]
            if (
                attr1 == "href"
                and attr2 == "title"
                and link.startswith("/source/")
            ):
                self.dictionary[link] = title


def parse_cantus_manuscript(url):
    contents = urllib.request.urlopen(url).read().decode("utf-8")
    cantusparser = CantusHTML()
    cantusparser.feed(contents)
    metadata = cantusparser.retrieve_metadata()
    return metadata


if __name__ == "__main__":
    if len(sys.argv) == 2:
        url = sys.argv[1]
        metadata = parse_cantus_manuscript(url)
        pprint(metadata)
    else:
        sources_url = "http://cantus.uwaterloo.ca/sources"
        root_url = "http://cantus.uwaterloo.ca"
        contents = urllib.request.urlopen(sources_url).read().decode("utf-8")
        parser = CantusAllSourcesHTML()
        parser.feed(contents)
        sources = parser.retrieve_sources()
        for link, name in sources.items():
            full_url = "{}{}".format(root_url, link)
            print(full_url, name)
            metadata = parse_cantus_manuscript(full_url)
            pprint(metadata)
            print()