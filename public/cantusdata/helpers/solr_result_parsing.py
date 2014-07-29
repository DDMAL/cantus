import re


def remove_unique_id(response_string):
    """
    Remove unique identifiers from solr responses.

    :param response_string:
    :return: string
    """
    return re.sub(r' ?"id": "[a-z\d-]*",?', '', response_string)

def remove_version_id(response_string):
    """
    Remove version numbers from solr responses.

    :param response_string:
    :return: string
    """
    return re.sub(r' ?"_version_": [\d]*,?', '', response_string)