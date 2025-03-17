from django.test import TestCase
from rest_framework import serializers

from city_pass.serializers.data_serializers import NotRequiredBlankToNullCharField


class TestNotRequiredBlankToNullCharField(TestCase):
    """Tests for the NotRequiredBlankToNullCharField serializer field."""

    def test_field_initialization(self):
        """Test that the field is initialized with correct attributes."""
        field = NotRequiredBlankToNullCharField()

        self.assertFalse(field.required)
        self.assertTrue(field.allow_null)
        self.assertTrue(field.allow_blank)

    def test_in_serializer_context(self):
        """Test the field in an actual serializer context."""

        class TestSerializer(serializers.Serializer):
            regular_field = serializers.CharField()
            optional_field = NotRequiredBlankToNullCharField()

        # Test with value
        data = {"regular_field": "value", "optional_field": "some value"}
        serializer = TestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data["optional_field"], "some value")

        # Test with empty string
        data = {"regular_field": "value", "optional_field": ""}
        serializer = TestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.data["optional_field"])

        # Test with None
        data = {"regular_field": "value", "optional_field": None}
        serializer = TestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.data["optional_field"])

        # Test with field omitted
        data = {"regular_field": "value"}
        serializer = TestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.data["optional_field"])
