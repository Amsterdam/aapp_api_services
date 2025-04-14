from django.utils import timezone
from rest_framework import serializers

from bridge.parking.serializers.general_serializers import (
    AmountCurrencySerializer,
    MillisecondsToSecondsSerializer,
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
    payment_zone_id = serializers.CharField()
    created_time = serializers.DateTimeField()
    parking_cost = ValueCurrencySerializer()
    is_cancelled = serializers.BooleanField()
    time_balance_applicable = serializers.BooleanField()
    money_balance_applicable = serializers.BooleanField()
    no_endtime = serializers.BooleanField()
    is_paid = serializers.BooleanField()


class ParkingSessionListPaginatedResponseSerializer(serializers.Serializer):
    result = ParkingSessionResponseSerializer(many=True)
    page = PaginationPageSerializer()
    _links = PaginationLinksSerializer()


class ParkingSessionOrderSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.IntegerField()
    payment_zone_id = serializers.CharField(required=False)
    vehicle_id = serializers.CharField()
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField(required=False)

    def validate(self, data):
        start = data.get("start_date_time")
        end = data.get("end_date_time")
        if start and end and end < start:
            raise serializers.ValidationError(
                "End date time must be after start date time"
            )
        return data


class ParkingSessionOrderUpdateSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.IntegerField()
    ps_right_id = serializers.IntegerField()
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField()


class FixedParkingSessionSerializer(SnakeToCamelCaseSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["parkingsession"] = data["parkingSession"]
        data.pop("parkingSession")
        return data


class ParkingSessionStartRequestSerializer(FixedParkingSessionSerializer):
    parking_session = ParkingSessionOrderSerializer()
    balance = AmountCurrencySerializer(required=False)
    redirect = RedirectSerializer(required=False)
    locale = serializers.CharField(required=False)


class ParkingSessionDeleteRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.IntegerField()
    ps_right_id = serializers.IntegerField()
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField(required=False)

    def to_representation(self, instance):
        instance["end_date_time"] = timezone.now()
        data = super().to_representation(instance)
        return {"parkingsession": data}


class ParkingSessionUpdateRequestSerializer(ParkingSessionStartRequestSerializer):
    parking_session = ParkingSessionOrderUpdateSerializer()


class ParkingSessionReceiptRequestSerializer(SnakeToCamelCaseSerializer):
    report_code = serializers.IntegerField()
    payment_zone_id = serializers.CharField()
    vehicle_id = serializers.CharField()
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField()

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
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    parking_time = MillisecondsToSecondsSerializer()
    remaining_parking_time = MillisecondsToSecondsSerializer()
    current_time_balance = MillisecondsToSecondsSerializer()
    remaining_time_balance = MillisecondsToSecondsSerializer()
    costs = ValueCurrencySerializer()
    costs_per_hour = ValueCurrencySerializer()
    current_wallet_balance = ValueCurrencySerializer()
    remaining_wallet_balance = ValueCurrencySerializer()
    regime_time = ReceiptRegimeTimeSerializer(many=True)
    remaining_time = MillisecondsToSecondsSerializer()
    report_code = serializers.IntegerField()
    payment_zone_id = serializers.CharField()
    payment_required = serializers.BooleanField()
    parking_cost = ValueCurrencySerializer()
