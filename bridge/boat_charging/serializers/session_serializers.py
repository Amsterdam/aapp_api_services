from rest_framework import serializers

from bridge.boat_charging.serializers.location_serializers import (
    LocationResponseSerializer,
)


class SessionResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    start_date_time = serializers.DateTimeField()
    end_date_time = serializers.DateTimeField(required=False)
    kwh = serializers.FloatField()
    evse_uid = serializers.CharField()
    connector_id = serializers.CharField()
    total_cost = serializers.FloatField(help_text="Excl VAT")
    currency = serializers.ChoiceField(choices=["USD", "EUR"])
    status = serializers.ChoiceField(choices=["ACTIVE", "COMPLETED"])


class TransactionSerializer(serializers.Serializer):
    id = serializers.CharField()
    charging_station_id = serializers.CharField()
    stop_reason = serializers.ChoiceField(choices=["LOCAL", "REMOTE"])
    force_stopped = serializers.BooleanField()


class SessionDetailResponseSerializer(SessionResponseSerializer):
    transaction = TransactionSerializer()
    location = LocationResponseSerializer()
