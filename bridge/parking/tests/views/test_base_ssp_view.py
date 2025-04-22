import json
from enum import Enum
from unittest.mock import patch
from urllib.parse import urlencode

from django.conf import settings
from requests import Response
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from bridge.parking.views.base_ssp_view import BaseSSPView
from core.tests.test_authentication import BasicAPITestCase


class DummyEnum(Enum):
    FOOBAR = "foobar"


class DummyRequestOptionalSerializer(serializers.Serializer):
    foo = serializers.CharField(required=False)
    bar = serializers.CharField(required=False)


class DummyRequestRequiredSerializer(serializers.Serializer):
    foo = serializers.CharField(required=True)
    bar = serializers.CharField(required=True)


class DummyResponseSerializer(serializers.Serializer):
    foobar = serializers.CharField()


class ExampleMinimalView(BaseSSPView):
    ssp_http_method = "get"
    ssp_endpoint = DummyEnum.FOOBAR

    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ExampleRequestSerializerView(BaseSSPView):
    serializer_class = DummyRequestRequiredSerializer
    response_serializer_class = DummyResponseSerializer
    ssp_endpoint = DummyEnum.FOOBAR

    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)

    def post(self, request, *args, **kwargs):
        return self.call_ssp(request)

    def patch(self, request, *args, **kwargs):
        return self.call_ssp(request)

    def put(self, request, *args, **kwargs):
        return self.call_ssp(request)

    def delete(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ExampleResponseSerializerView(BaseSSPView):
    response_serializer_class = DummyResponseSerializer
    ssp_http_method = "get"
    ssp_endpoint = DummyEnum.FOOBAR

    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ExamplePaginatedView(BaseSSPView):
    serializer_class = DummyRequestOptionalSerializer
    response_serializer_class = DummyResponseSerializer
    response_serializer_many = True
    response_key_selection = "foobar"
    ssp_http_method = "get"
    ssp_endpoint = DummyEnum.FOOBAR
    requires_access_token = True
    paginated = True

    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ExampleManyResponseSelectionView(BaseSSPView):
    serializer_class = DummyRequestOptionalSerializer
    response_serializer_class = DummyResponseSerializer
    response_serializer_many = True
    response_key_selection = "foobar"
    ssp_http_method = "get"
    ssp_endpoint = DummyEnum.FOOBAR

    def get(self, request, *args, **kwargs):
        return self.call_ssp(request)


class ExampleDictResponseSelectionView(BaseSSPView):
    serializer_class = DummyRequestOptionalSerializer
    response_serializer_class = DummyResponseSerializer
    response_serializer_many = False
    response_key_selection = "foobar"
    ssp_http_method = "get"
    ssp_endpoint = DummyEnum.FOOBAR

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


class TestEmptySSPResponse(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()

    @patch("bridge.parking.services.ssp.requests.request")
    def test_empty_ssp_response_empty_content(self, mock_request):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = b""

        mock_request.return_value = mock_response

        request = self.factory.get("/", headers=self.api_headers)
        response = ExampleMinimalView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_empty_ssp_response_ok_content(self, mock_request):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = b"OK"

        mock_request.return_value = mock_response

        request = self.factory.get("/", headers=self.api_headers)
        response = ExampleMinimalView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data)


class TestRequestSerializerView(BaseSSPTestCase):
    # TODO: test if _process_request_data is called correctly
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        self.view = ExampleRequestSerializerView()
        self.valid_request_data = {"foo": "hello", "bar": "world"}
        self.invalid_request_data = {"foo": "hello", "not_bar": "world"}

    def assert_request_data_is_valid(self, request, mock_request):
        response_data = {"foobar": "foo"}
        mock_request.return_value = self.create_ssp_response(200, response_data)

        response = ExampleRequestSerializerView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, response_data)

    def assert_request_data_is_invalid(self, request, mock_request):
        response_data = {"foobar": "foo"}
        mock_request.return_value = self.create_ssp_response(200, response_data)

        response = ExampleRequestSerializerView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "bar", status_code=400)
        self.assertContains(response, "This field is required", status_code=400)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_valid_request_data(self, mock_request):
        request = self.factory.get(
            "/", data=self.valid_request_data, headers=self.api_headers
        )
        self.assert_request_data_is_valid(request, mock_request)

        request = self.factory.post(
            "/", data=self.valid_request_data, headers=self.api_headers
        )
        self.assert_request_data_is_valid(request, mock_request)

        request = self.factory.patch(
            "/", data=self.valid_request_data, headers=self.api_headers
        )
        self.assert_request_data_is_valid(request, mock_request)

        request = self.factory.put(
            "/", data=self.valid_request_data, headers=self.api_headers
        )
        self.assert_request_data_is_valid(request, mock_request)

        request = self.factory.delete(
            f"/?{urlencode(self.valid_request_data)}",
            data=None,
            headers=self.api_headers,
        )
        self.assert_request_data_is_valid(request, mock_request)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_invalid_request_data(self, mock_request):
        request = self.factory.get(
            "/", data=self.invalid_request_data, headers=self.api_headers
        )
        self.assert_request_data_is_invalid(request, mock_request)

        request = self.factory.post(
            "/", data=self.invalid_request_data, headers=self.api_headers
        )
        self.assert_request_data_is_invalid(request, mock_request)

        request = self.factory.patch(
            "/", data=self.invalid_request_data, headers=self.api_headers
        )
        self.assert_request_data_is_invalid(request, mock_request)

        request = self.factory.put(
            "/", data=self.invalid_request_data, headers=self.api_headers
        )
        self.assert_request_data_is_invalid(request, mock_request)

        request = self.factory.delete(
            "/", data=self.invalid_request_data, headers=self.api_headers
        )
        self.assert_request_data_is_invalid(request, mock_request)

        request = self.factory.delete(
            f"/?{urlencode(self.invalid_request_data)}",
            data=None,
            headers=self.api_headers,
        )
        self.assert_request_data_is_invalid(request, mock_request)


class TestResponseSerializerView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        self.view = ExampleResponseSerializerView()

    @patch("bridge.parking.services.ssp.requests.request")
    def test_valid_response_data(self, mock_request):
        response_data = {"foobar": "foo"}
        mock_request.return_value = self.create_ssp_response(200, response_data)

        request = self.factory.get("/", headers=self.api_headers)
        response = self.view.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, response_data)

    @patch("bridge.parking.services.ssp.requests.request")
    def test_invalid_response_data(self, mock_request):
        mock_request.return_value = self.create_ssp_response(200, {"something": "else"})

        request = self.factory.get("/", headers=self.api_headers)
        response = self.view.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "foobar", status_code=400)
        self.assertContains(response, "This field is required", status_code=400)


class TestPaginatedSSPView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        self.view = ExamplePaginatedView()

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
            response = self.view.as_view()(request)
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
            "foobar": [],
            "meta": create_meta_pagination_data(total_items=0, total_pages=total_pages),
        }
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        request = self.factory.get(f"?page={total_pages + 1}", headers=self.api_headers)
        response = self.view.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["result"], [])

    @patch("bridge.parking.services.ssp.requests.request")
    def test_pagination_meta_data_missing(self, mock_request):
        mock_request.return_value = self.create_ssp_response(200, {"foobar": []})
        request = self.factory.get("/", headers=self.api_headers)
        response = self.view.as_view()(request)
        self.assertEqual(response.status_code, 400)


class TestResponseKeySelection(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()

    @patch("bridge.parking.services.ssp.requests.request")
    def test_response_key_selection_list_success(self, mock_request):
        mock_response_content = {
            "foobar": [
                {"foobar": "something"},
            ],
            "something": "else",
        }
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        request = self.factory.get("/", headers=self.api_headers)
        response = ExampleManyResponseSelectionView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, mock_response_content["foobar"])

    @patch("bridge.parking.services.ssp.requests.request")
    def test_response_key_selection_empty(self, mock_request):
        mock_response_content = {
            "foobar": [],
            "something": "else",
        }
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        request = self.factory.get("/", headers=self.api_headers)
        response = ExampleManyResponseSelectionView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    @patch("bridge.parking.services.ssp.requests.request")
    def test_response_key_selection_missing(self, mock_request):
        mock_response_content = {
            # "foobar" key with content is missing here
            "something": "else",
        }
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        request = self.factory.get("/", headers=self.api_headers)
        response = ExampleManyResponseSelectionView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    @patch("bridge.parking.services.ssp.requests.request")
    def test_response_key_selection_dict_success(self, mock_request):
        mock_response_content = {
            "foobar": {"foobar": "something"},
            "something": "else",
        }
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        request = self.factory.get("/", headers=self.api_headers)
        response = ExampleDictResponseSelectionView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, mock_response_content["foobar"])

    @patch("bridge.parking.services.ssp.requests.request")
    def test_response_key_selection_dict_missing(self, mock_request):
        mock_response_content = {
            # "foobar" key with content is missing here
            "something": "else",
        }
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        request = self.factory.get("/", headers=self.api_headers)
        response = ExampleDictResponseSelectionView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {})

    @patch("bridge.parking.services.ssp.requests.request")
    def test_response_key_selection_not_found_paginated(self, mock_request):
        mock_response_content = {
            # "foobar" is not present in the response
            "meta": create_meta_pagination_data(),
        }
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        request = self.factory.get("/", headers=self.api_headers)
        response = ExamplePaginatedView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["result"], [])
        self.assertIsNotNone(response.data["page"])
        self.assertIsNotNone(response.data["_links"])
