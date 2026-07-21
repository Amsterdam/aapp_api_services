from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from rest_framework import serializers

from core.validators import AappDeeplinkValidator


def validate_return_url(value):
    validators = (
        URLValidator(schemes=["http", "https"]),
        AappDeeplinkValidator(),
    )

    for validator in validators:
        try:
            validator(value)
            return value
        except DjangoValidationError:
            continue

    raise serializers.ValidationError("Enter a valid URL or deeplink.")


class SessionInitRequestSerializer(serializers.Serializer):
    station_id = serializers.CharField()
    socket_number = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    return_url = serializers.CharField(validators=[validate_return_url])


class SessionInitResponseSerializer(serializers.Serializer):
    checkout_url = serializers.URLField()
