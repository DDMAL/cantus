import math
from django.core.paginator import EmptyPage, PageNotAnInteger


# from http://code.google.com/p/solrpy/source/browse/solr/paginator.py
class SolrPaginator(object):
    """
    Create a Django-like Paginator for a solr response object. Can be handy
    when you want to hand off a Paginator and/or Page to a template to
    display results, and provide links to next page, etc.

    For example:
    >>> from solr import SolrConnection, SolrPaginator
    >>>
    >>> conn = SolrConnection('http://localhost:8083/solr')
    >>> response = conn.query('title:huckleberry')
    >>> paginator = SolrPaginator(response)
    >>> print paginator.num_pages
    >>> page = paginator.get_page(5)

    For more details see the Django Paginator documentation and solrpy
    unittests.

      http://docs.djangoproject.com/en/dev/topics/pagination/

    """

    def __init__(self, result, default_page_size=10, allow_empty_first_page=True):
        self.params = result.header['params']
        self.result = result
        self.query = result._query
        self.count = int(self.result.numFound)
        self.allow_empty_first_page = allow_empty_first_page

        if 'rows' in self.params:
            self.page_size = int(self.params['rows'])
        elif default_page_size:
            try:
                self.page_size = int(default_page_size)
            except ValueError:
                raise ValueError('default_page_size must be an integer')

            if self.page_size < len(self.result.results):
                raise ValueError('Invalid default_page_size specified, lower '
                                 'than number of results')

        else:
            self.page_size = len(self.result.results)

    def validate_number(self, number):
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger("That page number is not an integer")

        if number < 1:
            raise EmptyPage("That page number is less than 1")
        if number > self.num_pages:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage('That page contains no results')
        return number

    @property
    def num_pages(self):
        if self.count == 0:
            return 0
        return int(math.ceil(float(self.count) / float(self.page_size)))

    @property
    def page_range(self):
        """List the index numbers of the available result pages."""
        if self.count == 0:
            return []
        # Add one because range is right-side exclusive
        return range(1, self.num_pages + 1)

    def _fetch_page(self, start=0):
        """Retrieve a new result response from Solr."""
        # need to convert the keys to strings to pass them as parameters
        new_params = {}
        for k, v in self.params.items():
            new_params[str(k)] = v.encode('utf-8')

        # get the new start index
        new_params['start'] = start
        return self.query(**new_params)

    def page(self, page_num=1):
        """Return the requested Page object"""
        try:
            int(page_num)
        except:
            raise PageNotAnInteger

        if page_num not in self.page_range:
            raise EmptyPage('That page does not exist.')

        # Page 1 starts at 0; take one off before calculating
        start = (page_num - 1) * self.page_size
        new_result = self._fetch_page(start=start)
        return SolrPage(new_result.results, page_num, self)


# from http://code.google.com/p/solrpy/source/browse/solr/paginator.py
class SolrGroupedPaginator(object):
    """
    Create a Django-like Paginator for a solr response object. Can be handy
    when you want to hand off a Paginator and/or Page to a template to
    display results, and provide links to next page, etc.

    For example:
    >>> from solr import SolrConnection, SolrPaginator
    >>>
    >>> conn = SolrConnection('http://localhost:8083/solr')
    >>> response = conn.query('title:huckleberry')
    >>> paginator = SolrPaginator(response)
    >>> print paginator.num_pages
    >>> page = paginator.get_page(5)

    For more details see the Django Paginator documentation and solrpy
    unittests.

      http://docs.djangoproject.com/en/dev/topics/pagination/

    """

    def __init__(self, result, default_page_size=10, allow_empty_first_page=True):
        self.params = result.header['params']
        self.result = result
        self.query = result._query
        self.allow_empty_first_page = allow_empty_first_page
        self._num_pages = self._count = None

        self.group_field = self.params['group.field']
        self.matches = self.result.grouped[self.group_field]['matches']
        self.ngroups = self.result.grouped[self.group_field]['ngroups']

        self.count = self.ngroups

        if 'rows' in self.params:
            self.page_size = int(self.params['rows'])
        elif default_page_size:
            try:
                self.page_size = int(default_page_size)
            except ValueError:
                raise ValueError('default_page_size must be an integer')

            if self.page_size < len(self.result.results):
                raise ValueError('Invalid default_page_size specified, lower '
                                 'than number of results')

        else:
            self.page_size = len(self.result.results)

    @property
    def num_pages(self):
        if self.count == 0:
            return 0
        return int(math.ceil(float(self.count) / float(self.page_size)))

    @property
    def page_range(self):
        """List the index numbers of the available result pages."""
        if self.count == 0:
            return []
        # Add one because range is right-side exclusive
        return range(1, self.num_pages + 1)

    def validate_number(self, number):
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger("That page number is not an integer")

        if number < 1:
            raise EmptyPage("That page number is less than 1")
        if number > self.num_pages:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage('That page contains no results')
        return number

    def _fetch_page(self, start=0):
        """Retrieve a new result response from Solr."""
        # need to convert the keys to strings to pass them as parameters
        new_params = {}
        for k, v in self.params.items():
            new_params[str(k)] = v.encode('utf-8')

        # get the new start index
        new_params['start'] = start
        return self.query(**new_params)

    def page(self, page_num=1):
        """Return the requested Page object"""
        try:
            int(page_num)
        except:
            raise PageNotAnInteger

        if page_num not in self.page_range:
            raise EmptyPage('That page does not exist.')

        # Page 1 starts at 0; take one off before calculating
        start = (page_num - 1) * self.page_size
        new_result = self._fetch_page(start=start)
        grouped_results = [x['doclist'][0] for x in new_result.grouped[self.group_field]['groups']]
        return SolrPage(grouped_results, page_num, self)


class SolrPage(object):
    """A single Paginator-style page."""

    def __init__(self, result, number, paginator):
        self.result = result
        self.number = number
        self.paginator = paginator
        self.object_list = [SolrResponseObject(**s) for s in self.result]

    def __repr__(self):
        return '<Page %s of %s>' % (self.number, self.paginator.num_pages)

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        return list(self.object_list)[index]

    def __iter__(self):
        i = 0
        try:
            while True:
                v = self[i]
                yield v
                i += 1
        except IndexError:
            return

    def __contains__(self, value):
        for v in self:
            if v == value:
                return True
            return False

    def index(self, value):
        for i, v in enumerate(self):
            if v == value:
                return i
        raise ValueError

    def count(self, value):
        return sum([1 for v in self if v == value])

    def has_next(self):
        return self.number < self.paginator.num_pages

    def has_previous(self):
        return self.number > 1

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def start_index(self):
        # off by one because self.number is 1-based w/django,
        # but start is 0-based in solr
        return (self.number - 1) * self.paginator.page_size

    def end_index(self):
        # off by one because we want the last one in this set,
        # not the next after that, to match django paginator
        return self.start_index() + len(self.result) - 1

    def next_page_number(self):
        return self.paginator.validate_number(self.number + 1)

    def previous_page_number(self):
        return self.paginator.validate_number(self.number - 1)


class SolrResponseObject(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)
