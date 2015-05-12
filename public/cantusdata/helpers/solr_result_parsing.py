import re


def remove_all_solr_metadata(response_string):
    """
    Remove all of the Solr metadata fields from a response.

    :param response_string:
    :return:
    """
    response_string = remove_unique_id(response_string)
    response_string = remove_number(response_string, "_version_")
    response_string = remove_number(response_string, "score")
    return response_string

def remove_unique_id(response_string):
    """
    Remove unique identifiers from solr responses.

    :param response_string:
    :return: string
    """
    return re.sub(r',?\s*"id":\s*"[a-z\d-]*"', '', response_string)

def remove_number(response_string, parameter_name):
    """
    Remove numbers from solr responses.

    :param response_string:
    :return: string
    """
    return re.sub(r',?\s*"{0}":\s*[\d\.]*'.format(parameter_name),
                  '', response_string)
