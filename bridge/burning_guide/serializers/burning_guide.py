import re

from rest_framework import serializers

postal_code_pattern = re.compile(r"\d{4}\s?([a-z]{2}|[A-Z]{2})")


class BurningGuideRequestSerializer(serializers.Serializer):
    postal_code = serializers.CharField(required=True)

    def validate_postal_code(self, value):
        if postal_code_pattern.match(value) is None:
            raise serializers.ValidationError(
                "postal code must be in '1234AB' or '1234 AB' format."
            )

        # get digits from postal_code
        postal_code_digits = int(value[:4])
        if (
            postal_code_digits < 1011 or postal_code_digits > 1109
        ) and postal_code_digits not in [1380, 1381, 1382, 1383, 1384]:
            raise serializers.ValidationError(
                "postal code must be part of the municipality of Amsterdam."
            )
        return value


class BruningGuideResponseSerializer(serializers.Serializer):
    postal_code = serializers.CharField()
    model_runtime = serializers.CharField()
    lki = serializers.IntegerField()
    wind = serializers.FloatField()
    wind_bft = serializers.IntegerField()
    advice_0 = serializers.IntegerField()
    advice_6 = serializers.IntegerField()
    advice_12 = serializers.IntegerField()
    advice_18 = serializers.IntegerField()
    definitive_0 = serializers.BooleanField()
    definitive_6 = serializers.BooleanField()
    definitive_12 = serializers.BooleanField()
    definitive_18 = serializers.BooleanField()
    wind_direction = serializers.IntegerField()
