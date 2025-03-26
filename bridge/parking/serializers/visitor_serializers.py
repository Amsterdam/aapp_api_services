from rest_framework import serializers

from bridge.parking.serializers.general_serializers import (
    MillisecondsToSecondsSerializer,
    SecondsToMillisecondsSerializer,
)
from core.utils.serializer_utils import (
    CamelToSnakeCaseSerializer,
    SnakeToCamelCaseSerializer,
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


class VisitorSessionRequestSerializer(SnakeToCamelCaseSerializer):
    vehicle_id = serializers.CharField()


class VisitorSessionSerializer(CamelToSnakeCaseSerializer):
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    vehicle_id = serializers.CharField()
    status = serializers.CharField()
    ps_right_id = serializers.CharField(required=False)
    visitor_name = serializers.CharField(required=False)
    remaining_time = serializers.IntegerField()
    report_code = serializers.CharField()
    payment_zone_id = serializers.CharField()
    time_balance_applicable = serializers.BooleanField()
    money_balance_applicable = serializers.BooleanField()
    no_endtime = serializers.BooleanField()


class VisitorSessionResponseSerializer(CamelToSnakeCaseSerializer):
    parking_session = VisitorSessionSerializer(many=True, required=False)
