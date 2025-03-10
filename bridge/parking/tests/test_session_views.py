from unittest.mock import patch

from django.urls import reverse

from bridge.parking.serializers.session_serializers import (
    ParkingSessionResponseSerializer,
)
from bridge.parking.tests.test_base_ssp_view import (
    BaseSSPTestCase,
    create_meta_pagination_data,
)
from core.utils.serializer_utils import create_serializer_data


class TestParkingSessionListView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-sessions")

    @patch("bridge.parking.services.ssp.requests.request")
    def test_get_list_result_successfully(self, mock_request):
        single_parking_session_item_dict = create_serializer_data(
            ParkingSessionResponseSerializer
        )
        parking_session_item_list = [single_parking_session_item_dict]
        mock_response_content = {
            "parkingSession": parking_session_item_list,
            "meta": create_meta_pagination_data(),
            "totalActiveParkingSessions": 1,
            "totalUpcomingParkingSessions": 0,
            "totalFinishedParkingSessions": 0,
        }
        mock_request.return_value = self.create_ssp_response(200, mock_response_content)

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["result"], parking_session_item_list)
