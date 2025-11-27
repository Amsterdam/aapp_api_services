from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from bridge.parking.enums import NotificationStatus
from bridge.parking.serializers.general_serializers import (
    AmountCurrencySerializer,
    RedirectSerializer,
    ValueCurrencySerializer,
)
from bridge.parking.serializers.pagination_serializers import (
    PaginationLinksSerializer,
    PaginationPageSerializer,
)
from bridge.parking.utils import validate_digits


class ParkingSessionListRequestSerializer(serializers.Serializer):
    STATUS_CHOICES = ["ACTIVE", "PLANNED", "COMPLETED", "CANCELLED"]

    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(
        required=False, min_value=1, max_value=100, default=10
    )
    sort = serializers.CharField(default="started_at:desc")
    status = serializers.ChoiceField(required=False, choices=STATUS_CHOICES)
    report_code = serializers.CharField(required=False)
    vehicle_id = serializers.CharField(required=False)

    def validate_report_code(self, value):
        # check that report_code contains only digits
        if value:
            value = validate_digits("report_code", value)
        return value


class ParkingSessionActivateRequestSerializer(serializers.Serializer):
    report_code = serializers.CharField(required=True)
    vehicle_id = serializers.CharField(required=True)

    def validate_report_code(self, value):
        # check that report_code contains only digits
        value = validate_digits("report_code", value)
        return value


class ParkingSessionActivateResponseSerializer(serializers.Serializer):
    ps_right_id = serializers.CharField()


class ParkingSessionResponseSerializer(serializers.Serializer):
    STATUS_CHOICES = ["ACTIVE", "PLANNED", "COMPLETED", "CANCELLED"]

    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField()
    vehicle_id = serializers.CharField()
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    ps_right_id = serializers.CharField(required=False)
    visitor_name = serializers.CharField(
        allow_blank=True, required=False, help_text="DEPRECATED"
    )
    remaining_time = serializers.IntegerField(help_text="DEPRECATED")
    report_code = serializers.CharField()
    payment_zone_id = serializers.CharField(required=False, help_text="DEPRECATED")
    payment_zone_name = serializers.CharField()
    parking_machine = serializers.CharField(required=True, allow_null=True)
    created_date_time = serializers.DateTimeField()
    parking_cost = ValueCurrencySerializer()
    is_cancelled = serializers.BooleanField()
    time_balance_applicable = serializers.BooleanField(
        required=False, help_text="DEPRECATED"
    )
    money_balance_applicable = serializers.BooleanField(
        required=False, help_text="DEPRECATED"
    )
    no_endtime = serializers.BooleanField()
    is_paid = serializers.BooleanField(required=True)
    can_edit = serializers.BooleanField()

    def to_internal_value(self, data):
        if isinstance(data, dict):
            if "createdTime" in data:
                data["createdDateTime"] = data.pop("createdTime")
            data["status"] = self.map_status(data.get("status"))
        return super().to_internal_value(data)

    def map_status(self, status: str) -> str:
        status_mapping = {
            "ACTIVE": "ACTIVE",
            "COMPLETED": "COMPLETED",
            "CANCELLED": "CANCELLED",
            "FUTURE": "PLANNED",
        }
        return status_mapping.get(status, status)


class ParkingSessionListPaginatedResponseSerializer(serializers.Serializer):
    result = ParkingSessionResponseSerializer(many=True)
    page = PaginationPageSerializer()
    _links = PaginationLinksSerializer(required=False, help_text="DEPRECATED")


class ParkingSessionOrderStartRequestSerializer(serializers.Serializer):
    report_code = serializers.CharField(required=False, help_text="DEPRECATED")
    payment_zone_id = serializers.CharField(required=False)
    vehicle_id = serializers.CharField()
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField(required=False)
    parking_machine = serializers.CharField(required=False)
    parking_machine_favorite = serializers.BooleanField(required=False, default=False)

    def validate_start_date_time(self, value):
        if value < timezone.now() - timedelta(minutes=1):
            raise serializers.ValidationError("Start time cannot be in the past.")
        return value

    def validate(self, data):
        # check that end_date_time is after start_date_time
        start = data.get("start_date_time")
        end = data.get("end_date_time")
        if start and end and end < start:
            raise serializers.ValidationError(
                "End date time must be after start date time"
            )

        # check payment_zone_id and parking_machine are never both provided
        zone = data.get("payment_zone_id")
        machine = data.get("parking_machine")
        if bool(zone) and bool(machine):
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "It is not allowed to provide both payment_zone_id and parking_machine."
                    ]
                }
            )

        return data

    def validate_report_code(self, value):
        # check that report_code contains only digits
        if value:
            value = validate_digits("report_code", value)
        return value

    def validate_payment_zone_id(self, value):
        # check that payment_zone_id contains only digits
        if value:
            value = validate_digits("payment_zone_id", value)
        return value

    def validate_parking_machine(self, value):
        # check that parking_machine contains only digits
        if value:
            value = validate_digits("parking_machine", value)
        return value


class ParkingSessionStartRequestSerializer(serializers.Serializer):
    parking_session = ParkingSessionOrderStartRequestSerializer()
    payment_type = serializers.ChoiceField(
        required=False,
        choices=["IDEAL", "CARDS"],
        default="IDEAL",
        help_text="New in V2, default is IDEAL",
    )
    balance = AmountCurrencySerializer(required=False, help_text="DEPRECATED")
    redirect = RedirectSerializer(required=False, help_text="DEPRECATED")
    locale = serializers.CharField(required=False, help_text="DEPRECATED")


class ParkingSessionOrderUpdateRequestSerializer(serializers.Serializer):
    ps_right_id = serializers.CharField()
    end_date_time = serializers.DateTimeField()
    report_code = serializers.CharField(required=False, help_text="DEPRECATED")
    vehicle_id = serializers.CharField(required=False, help_text="DEPRECATED")
    start_date_time = serializers.DateTimeField(required=False, help_text="DEPRECATED")


class ParkingSessionUpdateRequestSerializer(ParkingSessionStartRequestSerializer):
    parking_session = ParkingSessionOrderUpdateRequestSerializer()


class ParkingSessionDeleteRequestSerializer(serializers.Serializer):
    ps_right_id = serializers.CharField()
    vehicle_id = serializers.CharField(required=False, help_text="DEPRECATED")


class ParkingSessionReceiptRequestSerializer(serializers.Serializer):
    report_code = serializers.CharField()
    payment_zone_id = serializers.CharField(required=False)
    parking_machine = serializers.CharField(required=False)
    vehicle_id = serializers.CharField(required=False, help_text="DEPRECATED")
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField()
    ps_right_id = serializers.CharField(required=False, help_text="DEPRECATED")

    def validate(self, data):
        # check that either payment_zone_id or parking_machine is provided, but not both
        zone = data.get("payment_zone_id")
        machine = data.get("parking_machine")
        if bool(zone) and bool(machine):
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "It is not allowed to provide both payment_zone_id and parking_machine."
                    ]
                }
            )

        # check that end date time is after start date time
        start = data.get("start_date_time")
        end = data.get("end_date_time")
        if end < start:
            raise serializers.ValidationError(
                {"end_date_time": "End date time must be after start date time."}
            )

        return data

    def validate_report_code(self, value):
        # check that report_code contains only digits
        value = validate_digits("report_code", value)
        return value

    def validate_payment_zone_id(self, value):
        # check that payment_zone_id contains only digits
        if value:
            value = validate_digits("payment_zone_id", value)
        return value

    def validate_parking_machine(self, value):
        # check that parking_machine contains only digits
        if value:
            value = validate_digits("parking_machine", value)
        return value


class ReceiptRegimeTimeSerializer(serializers.Serializer):
    id = serializers.CharField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()


class ParkingSessionReceiptResponseSerializer(serializers.Serializer):
    start_date_time = serializers.DateTimeField(required=False, help_text="DEPRECATED")
    end_date_time = serializers.DateTimeField(required=False, help_text="DEPRECATED")
    parking_time = serializers.IntegerField()
    remaining_parking_time = serializers.IntegerField(
        required=False, help_text="DEPRECATED"
    )
    current_time_balance = serializers.IntegerField(
        required=False, help_text="DEPRECATED"
    )
    remaining_time_balance = serializers.IntegerField(
        required=False, help_text="DEPRECATED"
    )
    costs = ValueCurrencySerializer()
    costs_per_hour = ValueCurrencySerializer(required=False, help_text="DEPRECATED")
    current_wallet_balance = ValueCurrencySerializer(
        required=False, help_text="DEPRECATED"
    )
    remaining_wallet_balance = ValueCurrencySerializer(
        required=False, help_text="DEPRECATED"
    )
    regime_time = ReceiptRegimeTimeSerializer(
        many=True, required=False, help_text="DEPRECATED"
    )
    remaining_time = serializers.IntegerField()
    report_code = serializers.CharField(required=False, help_text="DEPRECATED")
    payment_zone_id = serializers.CharField(required=False, help_text="DEPRECATED")
    payment_required = serializers.BooleanField(required=False, help_text="DEPRECATED")
    parking_cost = ValueCurrencySerializer()


class ParkingOrderResponseSerializer(serializers.Serializer):
    frontend_id = serializers.IntegerField(
        required=False, allow_null=True, help_text="DEPRECATED"
    )
    ps_right_id = serializers.CharField(
        required=False, allow_null=True, help_text="NEW in V2, only for user role"
    )
    redirect_url = serializers.URLField(
        required=False, allow_null=True, help_text="Only for visitor role"
    )
    order_status = serializers.CharField(allow_null=True, help_text="Nullable in V2")
    order_type = serializers.CharField(required=False, help_text="DEPRECATED")
    notification_status = serializers.ChoiceField(
        choices=[(s.name, s.value) for s in NotificationStatus], required=False
    )
