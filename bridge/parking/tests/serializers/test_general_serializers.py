from django.test import TestCase, override_settings
from rest_framework import serializers

from bridge.parking.serializers.general_serializers import (
    FlexibleDateTimeSerializer,
    MillisecondsToSecondsSerializer,
    SecondsToMillisecondsSerializer,
    StatusTranslationSerializer,
)


class TestStatusTranslationSerializer(TestCase):
    def setUp(self):
        self.enum_to_str_choices = [
            ("ACTIVE", "Actief"),
            ("INACTIVE", "Inactief"),
        ]

        self.str_to_enum_choices = [
            ("Actief", "ACTIVE"),
            ("Aan", "ACTIVE"),
            ("Inactief", "INACTIVE"),
            ("Uit", "INACTIVE"),
        ]

    def test_enum_to_str_success(self):
        class TestSerializer(serializers.Serializer):
            status = StatusTranslationSerializer(choices=self.enum_to_str_choices)

        serializer = TestSerializer(data={"status": "ACTIVE"})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data["status"], "Actief")

        serializer = TestSerializer(data={"status": "INACTIVE"})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data["status"], "Inactief")

    def test_enum_to_str_failure(self):
        class TestSerializer(serializers.Serializer):
            status = StatusTranslationSerializer(choices=self.enum_to_str_choices)

        serializer = TestSerializer(data={"status": "UNKNOWN"})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

        serializer = TestSerializer(data={"status": "Actief"})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_str_to_enum_success(self):
        class TestSerializer(serializers.Serializer):
            status = StatusTranslationSerializer(choices=self.str_to_enum_choices)

        serializer = TestSerializer(data={"status": "Actief"})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data["status"], "ACTIVE")

        serializer = TestSerializer(data={"status": "Aan"})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data["status"], "ACTIVE")

        serializer = TestSerializer(data={"status": "Inactief"})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data["status"], "INACTIVE")

        serializer = TestSerializer(data={"status": "Uit"})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data["status"], "INACTIVE")

    def test_str_to_enum_failure(self):
        class TestSerializer(serializers.Serializer):
            status = StatusTranslationSerializer(choices=self.str_to_enum_choices)

        serializer = TestSerializer(data={"status": "UNKNOWN"})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

        serializer = TestSerializer(data={"status": "ACTIVE"})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)


class TestMillisecondsToSecondsSerializer(TestCase):
    def test_success(self):
        class TestSerializer(serializers.Serializer):
            passed_time = MillisecondsToSecondsSerializer()

        serializer = TestSerializer(data={"passed_time": 10000})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data["passed_time"], 10)

        serializer = TestSerializer(data={"passed_time": 1000})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data["passed_time"], 1)

        serializer = TestSerializer(data={"passed_time": 500})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data["passed_time"], 1)

    def test_failure(self):
        class TestSerializer(serializers.Serializer):
            passed_time = MillisecondsToSecondsSerializer()

        serializer = TestSerializer(data={"passed_time": "string"})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

        serializer = TestSerializer(data={"passed_time": 1000.5})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)


class TestSecondsToMillisecondsSerializer(TestCase):
    def test_success(self):
        class TestSerializer(serializers.Serializer):
            passed_time = SecondsToMillisecondsSerializer()

        serializer = TestSerializer(data={"passed_time": 10})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data["passed_time"], 10000)

        serializer = TestSerializer(data={"passed_time": 1})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data["passed_time"], 1000)

    def test_failure(self):
        class TestSerializer(serializers.Serializer):
            passed_time = SecondsToMillisecondsSerializer()

        serializer = TestSerializer(data={"passed_time": "string"})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

        serializer = TestSerializer(data={"passed_time": 10.5})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)


@override_settings(TIME_ZONE="Europe/Amsterdam")
class TestFlexibleDateTimeSerializer(TestCase):
    def test_success(self):
        valid_timestamps = [
            # UTC notations
            "2025-01-01T10:00:00Z",
            "2025-01-01T10:00:00.000Z",
            "2025-01-01T10:00:00+00:00",
            "2025-01-01T10:00:00.000+00:00",
            # Amsterdam timezone offset notations
            "2025-01-01T11:00:00+01:00",
            "2025-01-01T11:00:00.000+01:00",
            # None Amsterdam timezone offset notations
            "2025-01-01T12:00:00+02:00",
            "2025-01-01T12:00:00.000+02:00",
            "2025-01-01T08:00:00-02:00",
            "2025-01-01T08:00:00.000-02:00",
            # Assumed Amsterdam timezone offset notations
            "2025-01-01T11:00:00",
            "2025-01-01T11:00:00.000",
            # Missing T between date and time
            "2025-01-01 10:00:00.000Z",
            "2025-01-01 10:00:00.000+00:00",
            "2025-01-01 11:00:00.000+01:00",
            "2025-01-01 12:00:00.000+02:00",
            "2025-01-01 08:00:00.000-02:00",
        ]
        # First of January 2021 in Europe/Amsterdam (CEST/CET) timezone equals this:
        valid_timestamps_resolved = "2025-01-01T11:00:00+01:00"

        class TestSerializer(serializers.Serializer):
            timestamp = FlexibleDateTimeSerializer()

        for ts in valid_timestamps:
            serializer = TestSerializer(data={"timestamp": ts})
            serializer.is_valid(raise_exception=True)
            self.assertEqual(serializer.data["timestamp"], valid_timestamps_resolved)

    def test_failure(self):
        invalid_timestamps = [
            # Missing plus sign before offset
            "2025-01-01T11:00:00 01:00",
            "2025-01-01T11:00:00.000 01:00",
            "2025-01-01 11:00:00.000 01:00",
            # Other invalid formats
            "2025-13-01T00:00:00Z",  # Invalid month
            "2025-02-30T00:00:00Z",  # Invalid day
            "2025-01-01T25:00:00Z",  # Invalid hour
            # Invalid timezone offsets
            "2025-01-01T00:00:00+25:00",
            # Non-ISO formats
            "01-01-2025 00:00:00",
            "2025/01/01 00:00:00",
            # Completely invalid
            "not a date",
            "2025",
            "",
        ]

        class TestSerializer(serializers.Serializer):
            timestamp = FlexibleDateTimeSerializer()

        for ts in invalid_timestamps:
            serializer = TestSerializer(data={"timestamp": ts})
            with self.assertRaises(serializers.ValidationError, msg=ts):
                serializer.is_valid(raise_exception=True)
