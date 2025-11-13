import json
from datetime import datetime

import responses
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from uritemplate import URITemplate

from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.tests.mock_data import (
    license_plate_add,
    license_plate_delete,
    license_plates,
    permit,
)
from bridge.parking.tests.views.test_base_ssp_view import BaseSSPTestCase


class TestParkingLicensePlateListView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-license-plates-list")
        self.test_response = license_plates.MOCK_RESPONSE

    def test_successful_visitor_holder(self):
        report_code = 10001

        # two calls are made, the first doesn't have any vrns, so falls back to favorite vrns
        url = URITemplate(SSPEndpoint.PERMIT.value).expand(permit_id=report_code)
        resp_first = responses.get(url, json=permit.MOCK_RESPONSE_VISITOR_HOLDER)
        resp_second = responses.get(
            SSPEndpoint.LICENSE_PLATES.value, json=self.test_response
        )

        response = self.client.get(
            self.url + f"?report_code={report_code}", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(resp_first.body).get("vrns", [])), 0)
        self.assertEqual(resp_second.call_count, 1)

    def test_successful_business(self):
        report_code = 10002

        # two calls are made, the first one does have some vrns, but also checks favorite vrns
        url = URITemplate(SSPEndpoint.PERMIT.value).expand(permit_id=report_code)

        resp_first = responses.get(url, json=permit.MOCK_RESPONSE_BUSINESS)
        resp_second = responses.get(
            SSPEndpoint.LICENSE_PLATES.value, json=self.test_response
        )

        response = self.client.get(
            self.url + f"?report_code={report_code}", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(resp_first.body).get("vrns", [])), 2)
        self.assertEqual(len(json.loads(resp_second.body).get("favorite_vrns", [])), 2)
        self.assertEqual(len(response.data), 4)

    def test_sucessful_informal_care(self):
        report_code = 10003

        # only one call is made, because can_start_parking_session is False
        url = URITemplate(SSPEndpoint.PERMIT.value).expand(permit_id=report_code)

        resp_first = responses.get(url, json=permit.MOCK_RESPONSE_INFORMAL_CARE)

        response = self.client.get(
            self.url + f"?report_code={report_code}", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(resp_first.body).get("vrns", [])), 2)
        self.assertEqual(len(response.data), 2)

        vrns = json.loads(resp_first.body).get("vrns", [])
        with freeze_time("2025-11-01 12:00"):
            for vrn in vrns:
                is_future = vrn["is_future"]
                activated_at = vrn["activated_at"]
                self.assertEqual(
                    is_future,
                    datetime.strptime(activated_at, "%Y-%m-%dT%H:%M:%S%z")
                    > timezone.now(),
                )

    def test_sucessful_ga_resident_passenger(self):
        report_code = 10004

        # only one call is made, because can_start_parking_session is False
        url = URITemplate(SSPEndpoint.PERMIT.value).expand(permit_id=report_code)

        resp_first = responses.get(url, json=permit.MOCK_RESPONSE_GA_RESIDENT_PASSENGER)

        response = self.client.get(
            self.url + f"?report_code={report_code}", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(resp_first.body).get("vrns", [])), 2)
        self.assertEqual(len(response.data), 2)

    def test_sucessful_ga_resident_driver(self):
        report_code = 10005

        # only one call is made, because can_start_parking_session is False
        url = URITemplate(SSPEndpoint.PERMIT.value).expand(permit_id=report_code)

        resp_first = responses.get(url, json=permit.MOCK_RESPONSE_GA_RESIDENT_DRIVER)

        response = self.client.get(
            self.url + f"?report_code={report_code}", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(resp_first.body).get("vrns", [])), 1)
        self.assertEqual(len(response.data), 1)


class TestParkingLicensePlatePostDeleteView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-license-plates-post-delete")
        self.add_payload = {"vehicle_id": "CD234D", "visitor_name": "Secondary vehicle"}
        self.test_add_response = license_plate_add.MOCK_RESPONSE
        self.test_delete_response = license_plate_delete.MOCK_RESPONSE

    def test_successful_add(self):
        resp = responses.post(
            SSPEndpoint.LICENSE_PLATE_ADD.value, json=self.test_add_response
        )

        response = self.client.post(
            self.url, self.add_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_successful_delete(self):
        license_id = "10000"
        url_template = SSPEndpoint.LICENSE_PLATE_DELETE.value
        url = URITemplate(url_template).expand(license_plate_id=license_id)
        resp = responses.delete(url, json=self.test_delete_response)

        response = self.client.delete(
            self.url, query_params={"id": license_id}, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
