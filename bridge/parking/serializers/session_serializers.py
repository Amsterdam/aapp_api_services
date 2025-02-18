from rest_framework import serializers

from bridge.parking.serializers.general_serializers import MoneyValueSerializer
from core.utils.serializer_utils import CamelToSnakeCaseSerializer


class ParkingSessionResponseSerializer(CamelToSnakeCaseSerializer):
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    vehicle_id = serializers.CharField()
    status = serializers.CharField()
    visitor_name = serializers.CharField()
    remaining_time = serializers.IntegerField()
    report_code = serializers.CharField()
    payment_zone_id = serializers.CharField()
    created_time = serializers.DateTimeField()
    parking_time = serializers.IntegerField()
    parking_cost = MoneyValueSerializer()
    is_cancelled = serializers.BooleanField()
    time_balance_applicable = serializers.BooleanField()
    money_balance_applicable = serializers.BooleanField()
    no_endtime = serializers.BooleanField()
