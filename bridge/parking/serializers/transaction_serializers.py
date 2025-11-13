import logging

from rest_framework import serializers

from bridge.parking.serializers.general_serializers import (
    AmountCurrencySerializer,
    RedirectSerializer,
    ValueCurrencySerializer,
)
from bridge.parking.serializers.pagination_serializers import (
    PaginationLinksSerializer,
    PaginationPageSerializer,
)
from bridge.parking.serializers.permit_serializer import DayScheduleSerializer

logger = logging.getLogger(__name__)


class TransactionBalanceRequestSerializer(serializers.Serializer):
    payment_type = serializers.ChoiceField(
        choices=["IDEAL", "CARDS"],
        default="IDEAL",
        help_text="New in V2, default is IDEAL",
    )
    balance = AmountCurrencySerializer()
    redirect = RedirectSerializer(required=False, help_text="DEPRECATED")
    locale = serializers.ChoiceField(choices=["nl", "en", "fr", "de"], default="nl")


class TransactionBalanceResponseSerializer(serializers.Serializer):
    frontend_id = serializers.IntegerField(required=False, help_text="DEPRECATED")
    order_status = serializers.CharField(required=False, help_text="DEPRECATED")
    redirect_url = serializers.URLField(
        help_text="The URL to redirect the user to for payment"
    )
    order_type = serializers.CharField(required=False, help_text="DEPRECATED")


class TransactionBalanceConfirmRequestSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    status = serializers.CharField()
    signature = serializers.CharField()


class TransactionListRequestSerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(
        required=False, min_value=1, max_value=100, default=10
    )
    sort = serializers.CharField(required=False, default="paid_at:desc")
    filter_status = serializers.CharField(required=False, default="COMPLETED")


class TransactionResponseSerializer(serializers.Serializer):
    order_type = serializers.CharField(required=True)
    permit_name = serializers.CharField(required=False, help_text="DEPRECATED")
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField(required=False, help_text="DEPRECATED")
    report_code = serializers.CharField(required=False, help_text="DEPRECATED")
    is_visitor = serializers.BooleanField(required=False, help_text="DEPRECATED")
    parking_time = serializers.IntegerField(required=False, help_text="DEPRECATED")
    vehicle_id = serializers.CharField(
        allow_blank=True, required=False, help_text="DEPRECATED"
    )
    visitor_name = serializers.CharField(
        allow_blank=True, required=False, help_text="DEPRECATED"
    )
    amount = ValueCurrencySerializer()
    is_cancelled = serializers.BooleanField()
    is_stopped_early = serializers.BooleanField(required=False, help_text="DEPRECATED")
    time_balance_applicable = serializers.BooleanField(
        required=False, help_text="DEPRECATED"
    )
    money_balance_applicable = serializers.BooleanField(
        required=False, help_text="DEPRECATED"
    )
    no_endtime = serializers.BooleanField(required=False, help_text="DEPRECATED")
    created_date_time = serializers.DateTimeField()
    updated_date_time = serializers.DateTimeField(allow_null=True)
    days = DayScheduleSerializer(many=True, required=False, help_text="DEPRECATED")
    is_paid = serializers.BooleanField()


class TransactionsListPaginatedResponseSerializer(serializers.Serializer):
    result = TransactionResponseSerializer(many=True)
    page = PaginationPageSerializer()
    _links = PaginationLinksSerializer(required=False, help_text="DEPRECATED")
