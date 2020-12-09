import urllib.parse
from django.conf import settings
import solr


class SolrSearch(object):
    """
    This class is a helper class for translating between query parameters
    in a GET request and the format needed to search in Solr.

    It has three main methods: search, facets, and group_search.

    The search method performs a search. The `parse_request` and
    `prepare_query` methods are automatically called with the request object
    when the class is initialized. This filters all the query keys and
    translates them to Solr.

    The facets method requests facets from the Solr search server.

    The group_search method performs a search, but can be used to group
    results on any given field.

    The private methods in this class (ones beginning in underscores) are
    helpers that do all the work.

    """

    def __init__(self, request, additional_query_params=None):
        self.server = solr.Solr(settings.SOLR_SERVER)
        # self.query_dict = query_dict
        self.request = request
        self.additional_query_params = additional_query_params
        self.parsed_request = {}
        self.prepared_query = ""
        self.solr_params = {}
        self._parse_request()
        self._prepare_query()

    def search(self, **kwargs):
        self.solr_params.update(kwargs)
        res = self._do_query()
        return res

    def facets(self, facet_fields, **kwargs):
        facet_params = {
            "facet": "true",
            "facet_field": facet_fields,
            "facet_mincount": 1,
        }
        self.solr_params.update(facet_params)
        self.solr_params.update(kwargs)

        res = self._do_query()
        return res

    def group_search(self, group_fields, **kwargs):
        group_params = {
            "group": "true",
            "group_ngroups": "true",
            "group_field": group_fields,
        }
        self.solr_params.update(group_params)
        self.solr_params.update(kwargs)

        res = self._do_query()
        return res

    def _do_query(self):
        return self.server.select(self.prepared_query, **self.solr_params)

    def _parse_request(self):
        qdict = self.request.GET
        for k, v in qdict.lists():
            self.parsed_request[k] = v

    def _prepare_query(self):
        arr = []
        if self.additional_query_params:
            for k, v in self.additional_query_params.items():
                arr.append("{0}:({1})".format(k, v))
        if self.parsed_request:
            for k, v in self.parsed_request.items():
                if not v:
                    continue
                if k == "q":
                    if v[0] != "":
                        arr.insert(0, "{0}".format(v[0]))
                elif k in ("start", "rows"):
                    # Start and row parameters are single integers
                    self.solr_params[k] = int(v[0])
                elif k == "sort":
                    # Treat sort as a string, not a one-element tuple
                    self.solr_params["sort"] = str(v[0])
                else:
                    arr.append(
                        "{0}:({1})".format(
                            k,
                            " OR ".join(
                                ['"{0}"'.format(s) for s in v if v is not None]
                            ),
                        )
                    )

        if arr:
            self.prepared_query = " AND ".join(arr)
        else:
            self.prepared_query = "*:*"


class SolrSearchQueryless(SolrSearch):
    def _parse_request(self):
        self.parsed_request = urllib.parse.parse_qs(self.request)
