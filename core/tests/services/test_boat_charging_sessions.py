from core.services.boat_charging_sessions import BoatChargingSessionService
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import BoatChargingSession
from notification.models.notification_models import Device


class TestBoatChargingSessionService(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.service = BoatChargingSessionService()

    def test_create_boat_charging_session(self):
        device_id = "foo"
        session_id = "bar"
        self.service.create_boat_charging_session(device_id, session_id)

        self.assertEqual(BoatChargingSession.objects.count(), 1)
        self.assertEqual(Device.objects.filter(external_id=device_id).exists(), True)
