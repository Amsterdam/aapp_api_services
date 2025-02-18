from rest_framework import serializers

from bridge.parking.serializers.general_serializers import MoneyValueSerializer
from core.utils.serializer_utils import CamelToSnakeCaseSerializer


class DayScheduleSerializer(CamelToSnakeCaseSerializer):
    day_of_week = serializers.CharField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()


class PaymentZoneSerializer(CamelToSnakeCaseSerializer):
    id = serializers.CharField()
    description = serializers.CharField()
    city = serializers.CharField()
    days = DayScheduleSerializer(many=True)


class PermitZoneSerializer(CamelToSnakeCaseSerializer):
    permit_zone_id = serializers.CharField()
    name = serializers.CharField()
    show_permit_zone_url = serializers.BooleanField(required=False)


class VisitorAccountSerializer(CamelToSnakeCaseSerializer):
    report_code = serializers.IntegerField()
    pin = serializers.CharField()
    minutes_remaining = serializers.IntegerField(required=False)


class PermitItemSerializer(CamelToSnakeCaseSerializer):
    report_code = serializers.IntegerField()
    time_balance = serializers.IntegerField()
    time_valid_until = serializers.DateTimeField(required=False)
    permit_type = serializers.CharField()
    discount = serializers.FloatField(required=False)
    permit_zone = PermitZoneSerializer()
    payment_zones = PaymentZoneSerializer(many=True)
    visitor_account = VisitorAccountSerializer(required=False)
    parking_rate = MoneyValueSerializer()
    parking_rate_original = MoneyValueSerializer()
    time_balance_applicable = serializers.BooleanField()
    money_balance_applicable = serializers.BooleanField()
    forced_license_plate_list = serializers.BooleanField()
    no_endtime = serializers.BooleanField()
    visitor_account_allowed = serializers.BooleanField()
    max_sessions_allowed = serializers.IntegerField()
    max_session_length_in_days = serializers.IntegerField(required=False)
    permit_name = serializers.CharField()
