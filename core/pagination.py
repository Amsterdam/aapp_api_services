from urllib.parse import urlencode

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"
    max_page_size = None
    page_size = 10

    @staticmethod
    def create_paginated_data(
        data,
        page_number,
        page_size,
        total_elements,
        total_pages,
        self_href,
        next_href,
        previous_href,
    ):
        pagination = {
            "number": page_number,
            "size": page_size,
            "totalElements": total_elements,
            "totalPages": total_pages,
        }

        links = {
            "self": {"href": self_href},
        }

        if next_href:
            links["next"] = {"href": next_href}

        if previous_href:
            links["previous"] = {"href": previous_href}

        return {
            "result": data,
            "page": pagination,
            "_links": links,
        }

    def get_paginated_response(self, data):
        request = self.request
        page_number = self.page.number
        page_size = self.get_page_size(request)
        total_elements = self.page.paginator.count
        total_pages = self.page.paginator.num_pages

        # Build base URI without pagination parameters
        base_uri = request.build_absolute_uri(request.path)
        query_params = request.query_params.copy()
        query_params.pop(self.page_query_param, None)
        query_params.pop(self.page_size_query_param, None)

        # Construct pagination links
        links = {"self": {"href": request.build_absolute_uri()}}
        next_href = None
        previous_href = None
        if self.page.has_next():
            next_page_number = self.page.next_page_number()
            next_query_params = query_params.copy()
            next_query_params[self.page_query_param] = next_page_number
            next_query_params[self.page_size_query_param] = page_size
            next_query_string = urlencode(next_query_params, doseq=True)
            next_href = f"{base_uri}?{next_query_string}"
        if self.page.has_previous():
            previous_page_number = self.page.previous_page_number()
            prev_query_params = query_params.copy()
            prev_query_params[self.page_query_param] = previous_page_number
            prev_query_params[self.page_size_query_param] = page_size
            prev_query_string = urlencode(prev_query_params, doseq=True)
            previous_href = f"{base_uri}?{prev_query_string}"

        paginated_data = self.create_paginated_data(
            data,
            page_number,
            page_size,
            total_elements,
            total_pages,
            links["self"]["href"],
            next_href,
            previous_href,
        )

        return Response(paginated_data)

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "result": schema,
                "page": {
                    "type": "object",
                    "properties": {
                        "number": {"type": "integer", "example": 2},
                        "size": {"type": "integer", "example": 10},
                        "totalElements": {"type": "integer", "example": 33},
                        "totalPages": {"type": "integer", "example": 4},
                    },
                },
                "_links": {
                    "type": "object",
                    "properties": {
                        "self": {
                            "type": "object",
                            "properties": {
                                "href": {
                                    "type": "string",
                                    "format": "uri",
                                    "example": "http://api.example.com/projects?page=2&page_size=10",
                                }
                            },
                        },
                        "next": {
                            "type": "object",
                            "properties": {
                                "href": {
                                    "type": "string",
                                    "format": "uri",
                                    "example": "http://api.example.com/projects?page=3&page_size=10",
                                }
                            },
                        },
                        "previous": {
                            "type": "object",
                            "properties": {
                                "href": {
                                    "type": "string",
                                    "format": "uri",
                                    "example": "http://api.example.com/projects?page=1&page_size=10",
                                }
                            },
                        },
                    },
                },
            },
        }
