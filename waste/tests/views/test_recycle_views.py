from django.urls import reverse
from model_bakery import baker

from core.tests.test_authentication import BasicAPITestCase
from waste.models import RecycleLocation


class TestRecycleLocationsView(BasicAPITestCase):
    def test_simple_recycle_location(self):
        recycling_point = baker.make(RecycleLocation)
        url = reverse("waste-recycle-locations")

        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], recycling_point.name)

    def test_caching(self):

        recycling_point = baker.make(RecycleLocation)
        url = reverse("waste-recycle-locations")

        # First call to populate cache
        response1 = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(len(response1.data), 1)

        # Delete the recycle location from the database
        RecycleLocation.objects.filter(id=recycling_point.id).delete()

        # Second call should still return the cached data
        response2 = self.client.get(url, headers=self.api_headers)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(len(response2.data), 1)

        # Third call should still throw an error
        response3 = self.client.get(
            url, headers={self.auth_instance.api_key_header: "not-valid"}
        )
        self.assertEqual(response3.status_code, 401)
