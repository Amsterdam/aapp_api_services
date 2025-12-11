from rest_framework import serializers

from bridge.utils import validate_digits


class PostalCodeValidationMixin:
    def validate_postal_code(self, value):
        value = validate_digits("postal_code", value)

        # get digits from postal_code
        postal_code_digits = int(value)
        if (
            postal_code_digits < 1011 or postal_code_digits > 1109
        ) and postal_code_digits not in [1380, 1381, 1382, 1383, 1384]:
            raise serializers.ValidationError(
                "postal code must be part of the municipality of Amsterdam."
            )
        return value
