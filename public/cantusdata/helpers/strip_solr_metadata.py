EXCLUDED_KEYS = ('_version_', 'score', 'id')


def strip_solr_metadata(doc):
    """Strip Solr-specific fields from a dict returned from a Solr query"""
    return {
        key: value for key, value in doc.items() if key not in EXCLUDED_KEYS
    }
