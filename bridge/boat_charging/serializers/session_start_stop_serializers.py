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
    vignette_id = serializers.IntegerField(required=False)
    vignette_number = serializers.CharField(required=False)
    postal_code = serializers.CharField(required=False)

    def validate(self, attrs):
        vignette_id = attrs.get("vignette_id")
        vignette_number = attrs.get("vignette_number")
        postal_code = attrs.get("postal_code")

        if not vignette_id and not (vignette_number and postal_code):
            raise serializers.ValidationError(
                "Either vignette_id or vignette_number and postal_code must be provided"
            )

        return attrs


class SessionInitResponseSerializer(serializers.Serializer):
    checkout_url = serializers.URLField()
