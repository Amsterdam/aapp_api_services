import re

from rest_framework import serializers

from bridge.parking.serializers.general_serializers import (
    ValueCurrencySerializer,
)

zone_pattern = re.compile(r"[0-2][0-9]:[0-6][0-9]")


class DayScheduleSerializer(serializers.Serializer):
    day_of_week = serializers.ChoiceField(
        choices=[
            "Maandag",
            "Dinsdag",
            "Woensdag",
            "Donderdag",
            "Vrijdag",
            "Zaterdag",
            "Zondag",
        ]
    )
    start_time = serializers.CharField(min_length=5, max_length=5)
    end_time = serializers.CharField(min_length=5, max_length=5)

    def validate(self, data):
        start_time = data.get("start_time")
        if zone_pattern.match(start_time) is None:
            raise serializers.ValidationError(
                {"start_time": "start_time must be in HH:MM format."}
            )

        end_time = data.get("end_time")
        if zone_pattern.match(end_time) is None:
            raise serializers.ValidationError(
                {"end_time": "end_time must be in HH:MM format."}
            )

        # Additional validation can be added here if needed
        return data


class PaymentZoneSerializer(serializers.Serializer):
    id = serializers.CharField()
    description = serializers.CharField()
    hourly_rate = serializers.CharField(allow_null=True)
    city = serializers.CharField(help_text="DEPRECATED")
    days = DayScheduleSerializer(many=True)


class PermitZoneSerializer(serializers.Serializer):
    permit_zone_id = serializers.CharField()
    name = serializers.CharField()
    show_permit_zone_url = serializers.BooleanField(
        required=False, help_text="DEPRECATED"
    )
    description = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )


class PermitGeoJSONSerializer(serializers.Serializer):
    geojson = serializers.JSONField()


class VisitorAccountSerializer(serializers.Serializer):
    report_code = serializers.CharField()
    pin = serializers.CharField()
    seconds_remaining = serializers.IntegerField(required=False)


class PermitsRequestSerializer(serializers.Serializer):
    STATUS_CHOICES = [
        ("ACTIVE", "Actief"),
        ("INACTIVE", "Inactief"),
    ]

    status = serializers.ChoiceField(
        required=False, choices=[STATUS_CHOICES], help_text="DEPRECATED OPTION"
    )


class PermitItemSerializer(serializers.Serializer):
    report_code = serializers.CharField()
    time_balance = serializers.IntegerField(allow_null=True)
    time_valid_until = serializers.DateTimeField(allow_null=True)
    parking_machine_favorite = serializers.CharField(allow_null=True)
    permit_type = serializers.CharField()
    discount = serializers.FloatField(required=False, help_text="DEPRECATED")
    permit_zone = PermitZoneSerializer(allow_null=True)
    payment_zones = PaymentZoneSerializer(many=True)
    visitor_account = VisitorAccountSerializer(required=False, allow_null=True)
    parking_rate = ValueCurrencySerializer()
    parking_rate_original = ValueCurrencySerializer(help_text="DEPRECATED")
    time_balance_applicable = serializers.BooleanField()
    money_balance_applicable = serializers.BooleanField()
    forced_license_plate_list = serializers.BooleanField()
    no_endtime = serializers.BooleanField()
    visitor_account_allowed = serializers.BooleanField()
    max_sessions_allowed = serializers.IntegerField(required=False)
    max_session_length_in_days = serializers.IntegerField(required=True)
    permit_name = serializers.CharField()
    can_select_zone = serializers.BooleanField()
