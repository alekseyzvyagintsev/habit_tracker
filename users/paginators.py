from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    Создадим простую реализацию постраничной навигации с использованием стандартной Django REST Framework-пагинации:
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
