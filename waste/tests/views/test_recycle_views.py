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
