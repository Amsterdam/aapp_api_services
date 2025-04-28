import math

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.utils import (
    OpenApiTypes,
)
from rest_framework import serializers

from bridge.parking.utils import parse_iso_datetime
from core.utils.serializer_utils import (
    CamelToSnakeCaseSerializer,
    SnakeToCamelCaseSerializer,
)
from core.validators import AappDeeplinkValidator


class ValueCurrencySerializer(CamelToSnakeCaseSerializer):
    value = serializers.FloatField()
    currency = serializers.CharField()


class AmountCurrencySerializer(SnakeToCamelCaseSerializer):
    amount = serializers.FloatField()
    currency = serializers.CharField()


class ParkingBalanceResponseSerializer(CamelToSnakeCaseSerializer):
    """
    order_status options:
    - Initiated
    - Processing
    - ...?

    order_type options:
    - Parking
    - Payment
    - Both
    - ...?
    """

    frontend_id = serializers.IntegerField()
    redirect_url = serializers.URLField(required=False)
    order_status = serializers.CharField()
    order_type = serializers.CharField()


class DeeplinkUrlField(serializers.CharField):
    def __init__(self, **kwargs):
        super().__init__(validators=[AappDeeplinkValidator()], **kwargs)


class DeeplinkUrlFieldAutoSchema(OpenApiSerializerFieldExtension):
    target_class = DeeplinkUrlField

    def map_serializer_field(self, auto_schema, direction):
        schema = build_basic_type(OpenApiTypes.STR)
        schema["example"] = "amsterdam://some-module/some-action"
        return schema


class RedirectSerializer(SnakeToCamelCaseSerializer):
    merchant_return_url = DeeplinkUrlField()


class StatusTranslationSerializer(serializers.ChoiceField):
    """
    Serializer for translating status values to Egis statuses.

    Choices should be a list of tuples,
    where the first element is the internal status value
    and the second element is the Egis status value.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.choices:
            raise serializers.ValidationError("choices is required")

    def to_representation(self, value):
        if not value:
            return None
        for k, v in self.choices.items():
            if k.upper() == value.upper():
                return v
        raise serializers.ValidationError(f"Invalid status: {value}")

    def to_internal_value(self, data):
        if not data:
            return None
        for key, _ in self.choices.items():
            if key.upper() == data.upper():
                return key
        raise serializers.ValidationError(f"Invalid status: {data}")


class MillisecondsToSecondsSerializer(serializers.IntegerField):
    def to_representation(self, milliseconds):
        return math.ceil(milliseconds / 1000)


class SecondsToMillisecondsSerializer(serializers.IntegerField):
    def to_representation(self, seconds):
        return seconds * 1000


class FlexibleDateTimeSerializer(serializers.DateTimeField):
    """
    Parses datetime strings using custom parser function.
    """

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                return parse_iso_datetime(data)
            except ValueError as e:
                raise serializers.ValidationError(str(e)) from e
        return super().to_internal_value(data)
