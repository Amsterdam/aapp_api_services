from rest_framework import serializers

from bridge.parking.serializers.general_serializers import (
    MillisecondsToSecondsSerializer,
    SecondsToMillisecondsSerializer,
)
from core.utils.serializer_utils import (
    CamelToSnakeCaseSerializer,
)


class VisitorTimeBalanceRequestSerializer(serializers.Serializer):
    report_code = serializers.CharField()
    seconds_to_transfer = SecondsToMillisecondsSerializer()

    def to_representation(self, instance):
        """Convert all keys from snake_case to camelCase"""
        result = super().to_representation(instance)
        mapping = {
            "report_code": "reportCode",
            "seconds_to_transfer": "millisecondsToTransfer",
        }
        return {mapping[key]: value for key, value in result.items()}


class VisitorTimeBalanceResponseSerializer(CamelToSnakeCaseSerializer):
    main_account = MillisecondsToSecondsSerializer()
    visitor_account = MillisecondsToSecondsSerializer()
