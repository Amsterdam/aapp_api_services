from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.utils import (
    OpenApiTypes,
)
from rest_framework import serializers

from core.validators import AappDeeplinkValidator


class ValueCurrencySerializer(serializers.Serializer):
    value = serializers.FloatField(allow_null=True)
    currency = serializers.CharField(help_text="DEPRECATED")


class AmountCurrencySerializer(serializers.Serializer):
    amount = serializers.FloatField(help_text="Amount in whole euros")
    currency = serializers.CharField(help_text="DEPRECATED", default="EUR")

    def validate_amount(self, value):
        # check that amount is a positive number
        if value <= 0:
            raise serializers.ValidationError({"amount": "Amount should be positive."})
        return value


class DeeplinkUrlField(serializers.CharField):
    def __init__(self, **kwargs):
        super().__init__(validators=[AappDeeplinkValidator()], **kwargs)


class DeeplinkUrlFieldAutoSchema(OpenApiSerializerFieldExtension):
    target_class = DeeplinkUrlField

    def map_serializer_field(self, auto_schema, direction):
        schema = build_basic_type(OpenApiTypes.STR)
        schema["example"] = "amsterdam://some-module/some-action"
        return schema


class RedirectSerializer(serializers.Serializer):
    merchant_return_url = DeeplinkUrlField()
