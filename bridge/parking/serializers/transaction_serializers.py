from rest_framework import serializers

from bridge.parking.serializers.general_serializers import (
    FlexibleDateTimeSerializer,
    MillisecondsToSecondsSerializer,
    ValueCurrencySerializer,
)
from bridge.parking.serializers.pagination_serializers import (
    PaginationLinksSerializer,
    PaginationPageSerializer,
)
from bridge.parking.serializers.permit_serializer import DayScheduleSerializer
from core.utils.serializer_utils import CamelToSnakeCaseSerializer


class TransactionResponseSerializer(CamelToSnakeCaseSerializer):
    order_type = serializers.CharField()
    permit_name = serializers.CharField(required=False)
    start_date_time = FlexibleDateTimeSerializer(required=False)
    end_date_time = FlexibleDateTimeSerializer(required=False)
    report_code = serializers.CharField(required=False)
    is_visitor = serializers.BooleanField(required=False)
    parking_time = MillisecondsToSecondsSerializer(required=False)
    vehicle_id = serializers.CharField(required=False)
    visitor_name = serializers.CharField(required=False)
    amount = ValueCurrencySerializer(required=False)
    is_cancelled = serializers.BooleanField(required=False)
    is_stopped_early = serializers.BooleanField(required=False)
    time_balance_applicable = serializers.BooleanField(required=False)
    money_balance_applicable = serializers.BooleanField(required=False)
    no_endtime = serializers.BooleanField(required=False)
    creation_time = FlexibleDateTimeSerializer(required=False)
    updated_time = FlexibleDateTimeSerializer(required=False)
    days = DayScheduleSerializer(many=True, required=False)
    is_paid = serializers.BooleanField(required=False)


class TransactionsListPaginatedResponseSerializer(CamelToSnakeCaseSerializer):
    result = TransactionResponseSerializer(many=True)
    page = PaginationPageSerializer()
    _links = PaginationLinksSerializer()
