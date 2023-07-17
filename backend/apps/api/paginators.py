from rest_framework.pagination import PageNumberPagination


class PageLimitPaginator(PageNumberPagination):
    """
    Paginator with query params: limit, page.

    Examples query:
    https://localhost/api/users?limit=5 (query limit on one pages)
    https://localhost/api/users?page=2
    """
    page_size_query_param = 'limit'
