import json
from enum import Enum
from unittest.mock import patch

from django.conf import settings
from requests import Response
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from bridge.parking.views.base_ssp_view import BaseSSPView
from core.tests.test_authentication import BasicAPITestCase


class DummyEnum(Enum):
    FOOBAR = "foobar"


class DummyRequestSerializer(serializers.Serializer):
    foo = serializers.CharField(required=False)
    bar = serializers.CharField(required=False)


class DummyResponseSerializer(serializers.Serializer):
    foobar = serializers.CharField()


class ExamplePaginatedView(BaseSSPView):
    serializer_class = DummyRequestSerializer
    response_serializer_class = DummyResponseSerializer
    response_serializer_many = True
    response_key_selection = "foobar"
    ssp_http_method = "get"
    ssp_endpoint = DummyEnum.FOOBAR
    requires_access_token = True
    paginated = True

    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)


def create_meta_pagination_data(
    total_items=1, page_size=10, current_page=1, total_pages=1
):
    meta_pagination_data = {
        "totalItems": total_items,
        "itemsPerPage": page_size,
        "pages": total_pages,
        "currentPage": current_page,
        "pagination": {
            "first": f"/parkingsessions?page=1&itemsPerPage={page_size}",
            "curr": f"/parkingsessions?page={current_page}&itemsPerPage={page_size}",
            "last": f"/parkingsessions?page={total_pages}&itemsPerPage={page_size}",
        },
    }
    if total_pages > current_page:
        meta_pagination_data["pagination"]["next"] = (
            f"/parkingsessions?page={current_page + 1}&itemsPerPage={page_size}"
        )
    if current_page > 1:
        meta_pagination_data["pagination"]["prev"] = (
            f"/parkingsessions?page={current_page - 1}&itemsPerPage={page_size}"
        )

    return meta_pagination_data


class BaseSSPTestCase(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.api_headers[settings.SSP_ACCESS_TOKEN_HEADER] = "fake-access-token"

    def create_ssp_response(self, status_code, content):
        mock_response = Response()
        mock_response.status_code = status_code
        mock_response._content = json.dumps(content).encode("utf-8")
        return mock_response


class TestPaginatedSSPView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()

    @patch("bridge.parking.services.ssp.requests.request")
    def test_functional_pagination(self, mock_request):
        page_size = 10
        total_items = 55
        total_pages = 6

        def perform_pagination_test(current_page, expected_next, expected_previous):
            mock_response_content = {
                "foobar": [
                    {"foobar": "foo"},
                    {"foobar": "bar"},
                ],
                "meta": create_meta_pagination_data(
                    total_items=total_items,
                    page_size=page_size,
                    current_page=current_page,
                    total_pages=total_pages,
                ),
            }
            mock_request.return_value = self.create_ssp_response(
                200, mock_response_content
            )

            extra_query_params = "&foo=test&bar=test"
            request = self.factory.get(
                f"?page={current_page}{extra_query_params}", headers=self.api_headers
            )
            response = ExamplePaginatedView.as_view()(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.data["page"],
                {
                    "number": current_page,
                    "size": page_size,
                    "totalElements": total_items,
                    "totalPages": total_pages,
                },
            )
            self.assertIsNotNone(response.data["_links"].get("self"))
            self.assertIn(extra_query_params, response.data["_links"]["self"]["href"])

            self.assertEqual(
                response.data["_links"].get("next") is not None, expected_next
            )
            if expected_next:
                self.assertIn(
                    extra_query_params, response.data["_links"]["next"]["href"]
                )
            self.assertEqual(
                response.data["_links"].get("previous") is not None, expected_previous
            )
            if expected_previous:
                self.assertIn(
                    extra_query_params, response.data["_links"]["previous"]["href"]
                )

        # Test the first page
        perform_pagination_test(1, expected_next=True, expected_previous=False)
        # Test the second page
        perform_pagination_test(2, expected_next=True, expected_previous=True)
        # Test the last page
        perform_pagination_test(
            total_pages, expected_next=False, expected_previous=True
        )

    @patch("bridge.parking.services.ssp.requests.request")
    def test_pagination_with_invalid_page_number(self, mock_request):
        total_pages = 10
        mock_response_content = {
            "parkingSession": [],
            "meta": create_meta_pagination_data(total_pages=total_pages),
        }
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        request = self.factory.get(f"?page={total_pages + 1}", headers=self.api_headers)
        response = ExamplePaginatedView.as_view()(request)
        self.assertEqual(response.status_code, 404)
