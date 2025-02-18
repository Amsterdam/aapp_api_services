from rest_framework import serializers

from core.utils.serializer_utils import CamelToSnakeCaseSerializer


class MoneyValueSerializer(CamelToSnakeCaseSerializer):
    value = serializers.FloatField()
    currency = serializers.CharField()
