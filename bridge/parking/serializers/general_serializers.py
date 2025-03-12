from rest_framework import serializers

from core.utils.serializer_utils import CamelToSnakeCaseSerializer


class ValueCurrencySerializer(CamelToSnakeCaseSerializer):
    value = serializers.FloatField()
    currency = serializers.CharField()


class AmountCurrencySerializer(CamelToSnakeCaseSerializer):
    amount = serializers.FloatField()
    currency = serializers.CharField()


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


class ParkingOrderResponseSerializer(CamelToSnakeCaseSerializer):
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
    order_status = serializers.CharField()
    order_type = serializers.CharField()


class RedirectSerializer(CamelToSnakeCaseSerializer):
    merchant_return_url = serializers.URLField()
