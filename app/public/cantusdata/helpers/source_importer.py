from urllib import request
import json

class SourceImporter:
    """
    Imports sources from CantusDB by way of its APIs.

    :param str cantus_db_base_url: the domain for CantusDB.
    """
    def __init__(self, cantus_db_base_url):
        self.cdb_base_url = cantus_db_base_url

    def request_source_ids(self):
        """
        Requests the IDs of all sources available in CantusDB
        
        :return: a list of character source ID's
        """
        sources_url = self.cdb_base_url + "/json-sources/"
        sources_response = request.urlopen(sources_url).read()
        sources_json = json.loads(sources_response)
        source_ids = sources_json.keys()
        return source_ids

    def request_source_data(self, source_id):
        """
        Requests data on an individual source in CantusDB using
        the /json-node/ endpoint.
        
        :param str source_id: the ID of the source in CantusDB
        :return: a parsed json object containing source data
        """
        source_url = self.cdb_base_url + "/json-node/" + source_id
        source_response = request.urlopen(source_url).read()
        source_json = json.loads(source_response)
        return source_json

    def source_json_extractor(source_json):
        """
        Extracts required elements for the CU Manuscript
        model from the API response json.

        :param json source_json: parsed json response from json-node api
        :return: a dictionary of Manuscript attributes
        """
        source_dict = {}
        source_dict["id"] = source_json["vid"]
        source_dict["name"] = source_json["title"]
        source_dict["siglum"] = source_json["field_siglum"]["und"][0]["value"]
        source_dict["date"] = source_json["field_date"]["und"][0]["value"]
        source_dict["provenance"] = source_json["field_provenance"]["und"][0]["value"]
        source_dict["description"] = source_json["field_summary"]["und"][0]["value"]
        return source_dict
        
    def collect_sources(self):
        """
        Collects data on all sources in CantusDB for for importing
        into Cantus Ultimus.

        :return: a list of dictionaries with metadata on each source
        """
        source_ids = self.request_source_ids()
        source_list = []
        for id in source_ids:
            source_json = self.request_source_data(id)
            source_attrs = self.source_json_extractor(source_json)
            source_list.append(source_attrs)
        return source_list
            
            
