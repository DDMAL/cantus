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
        sources_url = f"{self.cdb_base_url}/json-sources/"
        sources_response = request.urlopen(sources_url).read()
        sources_json = json.loads(sources_response)
        source_ids = sources_json.keys()
        return source_ids

    def download_source_data(self, source_id):
        """
        Requests data on an individual source in CantusDB using
        the /json-node/ endpoint.

        :param str source_id: the ID of the source in CantusDB
        :return: a parsed json object containing source data
        """
        source_url = f"{self.cdb_base_url}/json-node/{source_id}"
        source_response = request.urlopen(source_url).read()
        source_json = json.loads(source_response)
        return source_json

    def download_source_provenance(self, source_id):
        """
        Use Cantus Database's provenance export API to download the provenance
        name for a given source.
        """
        prov_json_url = f"{self.cdb_base_url}/provenance/{source_id}/json"
        prov_json_response = request.urlopen(prov_json_url).read()
        prov_json = json.loads(prov_json_response)
        return prov_json["name"]

    def extract_source_data(self, source_json):
        """
        Extracts required elements for the CU Manuscript
        model from the API response json.

        :param json source_json: parsed json response from json-node api
        :return: a dictionary of Manuscript attributes
        """
        source_dict = {}
        source_dict["id"] = source_json["id"]
        source_dict["name"] = source_json["title"]
        source_dict["siglum"] = source_json.get("siglum", "")
        source_dict["date"] = source_json.get("date", "")
        provenance_id = source_json.get("provenance_id", "")
        source_dict["provenance"] = self.download_source_provenance(provenance_id)
        source_dict["description"] = source_json.get("summary", "")
        return source_dict

    def get_source_data(self, source_id):
        """
        Given a source ID from CantusDB, returns a dictionary of
        source metadata required to create a Cantus Ultimus
        manuscript object.

        :param str source_id: the ID of the source in CantusDB
        :return: a dictionary of metadata for use in creating a
        Manuscript object in Cantus Ultimus
        """
        source_json = self.download_source_data(source_id)
        source_data = self.extract_source_data(source_json)
        return source_data
