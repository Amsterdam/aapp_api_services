import datetime
import re
import zoneinfo

from rest_framework import serializers


def create_serializer_data(serializer_class, **custom_data):
    """
    Creates a valid dictionary for a serializer by instantiating it with dummy data
    and getting its default field values.

    Custom data can override defaults.
    """
    # Create default data based on serializer fields
    default_data = {}
    serializer = serializer_class()

    for field_name, field in serializer.fields.items():
        # Check URL field first, as it inherits from CharField
        if isinstance(field, serializers.URLField):
            default_data[field_name] = "https://example.com"
        elif isinstance(field, serializers.CharField):
            default_data[field_name] = f"test_{field_name}"
        elif isinstance(field, serializers.IntegerField):
            default_data[field_name] = 1
        elif isinstance(field, serializers.FloatField):
            default_data[field_name] = 1.0
        elif isinstance(field, serializers.BooleanField):
            default_data[field_name] = False
        elif isinstance(field, serializers.DateTimeField):
            amsterdam_tz = zoneinfo.ZoneInfo("Europe/Amsterdam")
            default_data[field_name] = datetime.datetime.now(amsterdam_tz).isoformat()
        elif isinstance(field, serializers.ListSerializer):
            # Handle nested lists (many=True)
            default_data[field_name] = [create_serializer_data(field.child.__class__)]
        elif isinstance(field, serializers.Serializer):
            # Handle nested serializers
            default_data[field_name] = create_serializer_data(field.__class__)

    # Override defaults with custom data
    default_data.update(custom_data)
    return default_data


class CamelToSnakeCaseSerializer(serializers.Serializer):
    """
    Convert incoming CamelCase keys to snake_case keys.

    Globally adjust startDate and endDate to startDateTime and endDateTime.
    """

    def camel_to_snake_case(self, name):
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def to_internal_value(self, data):
        if isinstance(data, dict):
            if "startDate" in data:
                data["startDateTime"] = data.pop("startDate")
            if "endDate" in data:
                data["endDateTime"] = data.pop("endDate")

            data = {self.camel_to_snake_case(key): value for key, value in data.items()}
        return super().to_internal_value(data)


class SnakeToCamelCaseSerializer(serializers.Serializer):
    """
    Convert incoming snake_case keys to CamelCase keys.
    """

    def snake_to_camel_case(self, name):
        components = name.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def to_representation(self, instance):
        result = super().to_representation(instance)
        return {self.snake_to_camel_case(key): value for key, value in result.items()}
