from rest_framework.pagination import PageNumberPagination


class ListPagination(PageNumberPagination):
    """
    Pages for the browsable list endpoints, which would otherwise serialize a
    whole table (tens of thousands of chants) per request.
    """

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000
