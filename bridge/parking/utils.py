from rest_framework import serializers


def validate_digits(variable_name: str, value: str) -> dict:
    # check that variable contains only digits
    if not value.isdigit():
        raise serializers.ValidationError(
            {variable_name: f"{variable_name} must contain only digits."}
        )
    return value
