from rest_framework import serializers

from bridge.burning_guide.serializers.mixins import PostalCodeValidationMixin


class AdviceRequestSerializer(serializers.Serializer, PostalCodeValidationMixin):
    postal_code = serializers.CharField(required=True)


class AdviceResponseSerializer(serializers.Serializer):
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
