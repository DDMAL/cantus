import re


def remove_unique_id(response_string):
    """
    Remove unique identifiers from solr responses.

    :param response_string:
    :return: string
    """
    return re.sub(r' ?"id": "[a-z\d-]*",?', '', response_string)

def remove_number(response_string, parameter_name):
    """
    Remove numbers from solr responses.

    :param response_string:
    :return: string
    """
    return re.sub(r' ?"{0}": [\d\.]*,?'.format(parameter_name),
                  '', response_string)