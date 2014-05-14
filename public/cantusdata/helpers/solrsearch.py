from django.conf import settings
import solr


class SolrSearch(object):
    """
        This class is a helper class for translating between query parameters in a GET
        request and the format needed to search in Solr.

        It has three main methods: search, facets, and group_search.

        The search method performs a search. The `parse_request` and `prepare_query` methods
        are automatically called with the request object when the class is initialized. This
        filters all the query keys and translates them to Solr.

        The facets method requests facets from the Solr search server.

        The group_search method performs a search, but can be used to group results on any
        given field.

        The private methods in this class (ones beginning in underscores) are helpers that
        do all the work.

    """
    def __init__(self, request):
        self.server = solr.Solr(settings.SOLR_SERVER)
        self.request = request
        self.parsed_request = {}
        self.prepared_query = u""
        self.solr_params = {}
        self._parse_request()
        self._prepare_query()

    def search(self, **kwargs):
        self.solr_params.update(kwargs)
        res = self._do_query()
        return res

    def facets(self, facet_fields, **kwargs):
        facet_params = {
            'facet': 'true',
            'facet_field': facet_fields,
            'facet_mincount': 1
        }
        self.solr_params.update(facet_params)
        self.solr_params.update(kwargs)

        res = self._do_query()
        return res

    def group_search(self, group_fields, **kwargs):
        group_params = {
            'group': 'true',
            'group_ngroups': 'true',
            'group_field': group_fields
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
        if self.parsed_request:
            arr = []
            for k, v in self.parsed_request.iteritems():
                if not v:
                    continue
                if k == 'q':
                    if v[0] != u"":
                        arr.insert(0, u"{0}".format(v[0]))
                else:
                    arr.append(u"{0}:({1})".format(k, " OR ".join(["\"{0}\"".format(s) for s in v if v is not None])))
            self.prepared_query = u" AND ".join(arr)
        else:
            self.prepared_query = u"*:*"
