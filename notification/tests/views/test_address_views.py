from django.urls import reverse
from model_bakery import baker

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import BurningGuideDevice, WasteDevice


class TestAddressView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("notification-address")
        self.device_id = "test-device-id"
        self.api_headers["DeviceId"] = self.device_id

    def test_update_no_existing_address(self):
        data = {
            "bag_nummeraanduiding_id": "test-bag-id",
            "postal_code": "1023",
        }
        response = self.client.post(
            self.url, data, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            BurningGuideDevice.objects.filter(device_id=self.device_id).count(), 0
        )
        self.assertEqual(
            WasteDevice.objects.filter(device_id=self.device_id).count(), 0
        )

    def test_update_waste_existing_address(self):
        baker.make(
            WasteDevice, device_id=self.device_id, bag_nummeraanduiding_id="old-bag-id"
        )
        data = {
            "bag_nummeraanduiding_id": "new-bag-id",
            "postal_code": "1023",
        }
        response = self.client.post(
            self.url, data, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            WasteDevice.objects.filter(device_id=self.device_id)
            .first()
            .bag_nummeraanduiding_id,
            data["bag_nummeraanduiding_id"],
        )
        self.assertEqual(
            BurningGuideDevice.objects.filter(device_id=self.device_id).count(), 0
        )

    def test_update_burning_guide_existing_address(self):
        baker.make(BurningGuideDevice, device_id=self.device_id, postal_code="1091")
        data = {
            "bag_nummeraanduiding_id": "new-bag-id",
            "postal_code": "1024",
        }
        response = self.client.post(
            self.url, data, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            BurningGuideDevice.objects.filter(device_id=self.device_id)
            .first()
            .postal_code,
            data["postal_code"],
        )
        self.assertEqual(
            WasteDevice.objects.filter(device_id=self.device_id).count(), 0
        )

    def test_update_both_existing_addresses(self):
        baker.make(BurningGuideDevice, device_id=self.device_id, postal_code="1091")
        baker.make(
            WasteDevice, device_id=self.device_id, bag_nummeraanduiding_id="old-bag-id"
        )
        data = {
            "bag_nummeraanduiding_id": "new-bag-id",
            "postal_code": "1024",
        }
        response = self.client.post(
            self.url, data, format="json", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            BurningGuideDevice.objects.filter(device_id=self.device_id)
            .first()
            .postal_code,
            data["postal_code"],
        )
        self.assertEqual(
            WasteDevice.objects.filter(device_id=self.device_id)
            .first()
            .bag_nummeraanduiding_id,
            data["bag_nummeraanduiding_id"],
        )

    def test_delete_no_existing_address(self):
        response = self.client.delete(self.url, format="json", headers=self.api_headers)
        self.assertEqual(response.status_code, 204)

    def test_delete_waste_existing_address(self):
        baker.make(
            WasteDevice, device_id=self.device_id, bag_nummeraanduiding_id="old-bag-id"
        )
        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            WasteDevice.objects.filter(device_id=self.device_id)
            .first()
            .bag_nummeraanduiding_id,
            None,
        )

    def test_delete_burning_guide_existing_address(self):
        baker.make(BurningGuideDevice, device_id=self.device_id, postal_code="1091")
        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            BurningGuideDevice.objects.filter(device_id=self.device_id)
            .first()
            .postal_code,
            None,
        )

    def test_delete_both_existing_addresses(self):
        baker.make(BurningGuideDevice, device_id=self.device_id, postal_code="1091")
        baker.make(
            WasteDevice, device_id=self.device_id, bag_nummeraanduiding_id="old-bag-id"
        )
        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            BurningGuideDevice.objects.filter(device_id=self.device_id)
            .first()
            .postal_code,
            None,
        )
        self.assertEqual(
            WasteDevice.objects.filter(device_id=self.device_id)
            .first()
            .bag_nummeraanduiding_id,
            None,
        )
