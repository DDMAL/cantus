import urllib.parse

from cantusdata.helpers.solr_client import InstrumentedSolr, make_solr


class InvalidSearch(ValueError):
    """A search request with parameters that cannot be turned into a query."""


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

    metrics_operation = "search"

    def __init__(self, request, additional_query_params=None):
        self.server = make_solr(self.metrics_operation, cls=InstrumentedSolr)
        # self.query_dict = query_dict
        self.request = request
        self.additional_query_params = additional_query_params
        self.parsed_request = {}
        self.prepared_query = ""
        self.solr_params = {}
        # Restrictions the caller imposes (e.g. public:true). Sent as filter
        # queries, never joined to the user's query: a q starting with local
        # params ({!lucene v=...}) makes Solr ignore the rest of that string,
        # but cannot touch an fq. Kept out of solr_params, which views echo.
        self.filter_queries = []
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
        return self.server.select(
            self.prepared_query, fq=self.filter_queries, **self.solr_params
        )

    def _parse_request(self):
        qdict = self.request.GET
        for k, v in qdict.lists():
            self.parsed_request[k] = v

    def _prepare_query(self):
        arr = []
        if self.additional_query_params:
            for k, v in self.additional_query_params.items():
                self.filter_queries.append("{0}:({1})".format(k, v))
        if self.parsed_request:
            for k, v in self.parsed_request.items():
                if not v:
                    continue
                if k == "q":
                    if v[0] != "":
                        arr.insert(0, "{0}".format(v[0]))
                elif k == "format":
                    # DRF's format override (?format=json), not a field.
                    continue
                elif k in ("start", "rows"):
                    # Start and row parameters are single integers
                    if not v[0].isdigit():
                        raise InvalidSearch(
                            f"{k} must be a non-negative integer, not {v[0]!r}."
                        )
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
    metrics_operation = "glyph_set"

    def _parse_request(self):
        self.parsed_request = urllib.parse.parse_qs(self.request)
