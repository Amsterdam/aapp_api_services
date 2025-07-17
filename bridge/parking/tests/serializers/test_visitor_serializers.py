from django.test import TestCase

from bridge.parking.serializers.permit_serializer import VisitorAccountSerializer


class TestVisitorAccountSerializer(TestCase):
    def setUp(self):
        self.serializer_class = VisitorAccountSerializer

    def test_serializer_validates_data(self):
        source_data = {
            "reportCode": 123,
            "pin": "1234",
            "millisecondsRemaining": 1000,
        }
        serializer = self.serializer_class(data=source_data)
        serializer.is_valid(raise_exception=True)
        target_data = serializer.validated_data

        self.assertEqual(target_data["report_code"], "123")
        self.assertEqual(target_data["pin"], "1234")
        self.assertEqual(target_data["seconds_remaining"], 1)

    def test_missing_milliseconds_remaining_is_ok(self):
        source_data = {
            "reportCode": "0123",
            "pin": "1234",
        }
        serializer = self.serializer_class(data=source_data)
        serializer.is_valid(raise_exception=True)
        target_data = serializer.validated_data

        self.assertEqual(target_data["report_code"], "0123")
        self.assertEqual(target_data["pin"], "1234")
        self.assertFalse("seconds_remaining" in target_data)
