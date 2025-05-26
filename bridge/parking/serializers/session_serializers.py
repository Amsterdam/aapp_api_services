from django.utils import timezone
from rest_framework import serializers

from bridge.parking.enums import NotificationStatus
from bridge.parking.serializers.general_serializers import (
    AmountCurrencySerializer,
    FlexibleDateTimeSerializer,
    MillisecondsToSecondsSerializer,
    ParkingBalanceResponseSerializer,
    RedirectSerializer,
    StatusTranslationSerializer,
    ValueCurrencySerializer,
)
from bridge.parking.serializers.pagination_serializers import (
    PaginationLinksSerializer,
    PaginationPageSerializer,
)
from core.utils.serializer_utils import (
    CamelToSnakeCaseSerializer,
    SnakeToCamelCaseSerializer,
)


class ParkingSessionListRequestSerializer(SnakeToCamelCaseSerializer):
    STATUS_CHOICES = [
        ("ACTIVE", "Actief"),
        ("PLANNED", "Toekomstig"),
        ("COMPLETED", "Voltooid"),
        ("CANCELLED", "Geannuleerd"),
    ]

    status = StatusTranslationSerializer(required=False, choices=STATUS_CHOICES)
    report_code = serializers.CharField(required=False)


class ParkingSessionResponseSerializer(CamelToSnakeCaseSerializer):
    STATUS_CHOICES = [
        ("Actief", "ACTIVE"),
        ("Gepland", "PLANNED"),
        ("Toekomstig", "PLANNED"),
        ("Voltooid", "COMPLETED"),
        ("Geannuleerd", "CANCELLED"),
    ]

    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField()
    vehicle_id = serializers.CharField()
    status = StatusTranslationSerializer(choices=STATUS_CHOICES)
    ps_right_id = serializers.CharField(required=False)
    visitor_name = serializers.CharField(required=False)
    remaining_time = serializers.IntegerField()
    report_code = serializers.CharField()
    payment_zone_id = serializers.CharField(required=False)
    created_date_time = serializers.DateTimeField()
    parking_cost = ValueCurrencySerializer()
    is_cancelled = serializers.BooleanField()
    time_balance_applicable = serializers.BooleanField()
    money_balance_applicable = serializers.BooleanField()
    no_endtime = serializers.BooleanField()
    is_paid = serializers.BooleanField()

    def to_internal_value(self, data):
        if isinstance(data, dict):
            if "createdTime" in data:
                data["createdDateTime"] = data.pop("createdTime")
        return super().to_internal_value(data)


class ParkingSessionListPaginatedResponseSerializer(serializers.Serializer):
    result = ParkingSessionResponseSerializer(many=True)
    page = PaginationPageSerializer()
    _links = PaginationLinksSerializer()


class ParkingSessionOrderStartRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.IntegerField()
    payment_zone_id = serializers.CharField(required=False)
    vehicle_id = serializers.CharField()
    start_date_time = FlexibleDateTimeSerializer()
    end_date_time = FlexibleDateTimeSerializer(required=False)

    def validate(self, data):
        start = data.get("start_date_time")
        end = data.get("end_date_time")
        if start and end and end < start:
            raise serializers.ValidationError(
                "End date time must be after start date time"
            )
        return data


class ParkingSessionStartRequestSerializer(SnakeToCamelCaseSerializer):
    parking_session = ParkingSessionOrderStartRequestSerializer()
    balance = AmountCurrencySerializer(required=False)
    redirect = RedirectSerializer(required=False)
    locale = serializers.CharField(required=False)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["parkingsession"] = data["parkingSession"]
        data.pop("parkingSession")
        return data


class ParkingSessionOrderUpdateRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.IntegerField()
    ps_right_id = serializers.IntegerField()
    start_date_time = FlexibleDateTimeSerializer()
    end_date_time = FlexibleDateTimeSerializer()


class ParkingSessionUpdateRequestSerializer(ParkingSessionStartRequestSerializer):
    parking_session = ParkingSessionOrderUpdateRequestSerializer()


class ParkingSessionDeleteRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.IntegerField()
    ps_right_id = serializers.IntegerField()
    start_date_time = FlexibleDateTimeSerializer()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["endDateTime"] = timezone.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return {"parkingsession": data}


class ParkingSessionReceiptRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.IntegerField()
    payment_zone_id = serializers.CharField()
    vehicle_id = serializers.CharField()
    start_date_time = FlexibleDateTimeSerializer()
    end_date_time = FlexibleDateTimeSerializer()

    def to_representation(self, instance):
        """
        Equalize input keys to other serializers,
        by converting outgoing startDateTime and endDateTime to startDate and endDate.
        """
        data = super().to_representation(instance)
        data["startDate"] = data.pop("startDateTime")
        data["endDate"] = data.pop("endDateTime")
        return data


class ReceiptRegimeTimeSerializer(CamelToSnakeCaseSerializer):
    id = serializers.CharField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()


class ParkingSessionReceiptResponseSerializer(CamelToSnakeCaseSerializer):
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField()
    parking_time = MillisecondsToSecondsSerializer()
    remaining_parking_time = MillisecondsToSecondsSerializer()
    current_time_balance = MillisecondsToSecondsSerializer(required=False)
    remaining_time_balance = MillisecondsToSecondsSerializer(required=False)
    costs = ValueCurrencySerializer()
    costs_per_hour = ValueCurrencySerializer()
    current_wallet_balance = ValueCurrencySerializer(required=False)
    remaining_wallet_balance = ValueCurrencySerializer(required=False)
    regime_time = ReceiptRegimeTimeSerializer(many=True, required=False)
    remaining_time = MillisecondsToSecondsSerializer()
    report_code = serializers.IntegerField()
    payment_zone_id = serializers.CharField()
    payment_required = serializers.BooleanField()
    parking_cost = ValueCurrencySerializer()

    def to_internal_value(self, data):
        if isinstance(data, dict):
            if "startTime" in data:
                data["startDateTime"] = data.pop("startTime")
            if "endTime" in data:
                data["endDateTime"] = data.pop("endTime")
        return super().to_internal_value(data)


class ParkingOrderResponseSerializer(ParkingBalanceResponseSerializer):
    notification_status = serializers.ChoiceField(
        choices=[(s.name, s.value) for s in NotificationStatus], required=False
    )
