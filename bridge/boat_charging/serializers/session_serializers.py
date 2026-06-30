from rest_framework import serializers

from bridge.boat_charging.serializers.location_serializers import (
    LocationPropertiesSerializer,
)


class SessionResponseSerializer(serializers.Serializer):
    # NRG data
    id = serializers.CharField()
    station_id = serializers.CharField()
    socket_number = serializers.CharField()
    nrg_status = serializers.ChoiceField(
        choices=(
            (1, "Created"),
            (2, "CheckedOut"),
            (3, "Charging"),
            (4, "Completed"),
            (5, "Cancelled"),
        )
    )
    created_date_time = serializers.DateTimeField()
    # CPMS data
    start_date_time = serializers.DateTimeField(allow_null=True)
    end_date_time = serializers.DateTimeField(allow_null=True)
    kwh = serializers.FloatField(allow_null=True)
    status = serializers.ChoiceField(choices=["ACTIVE", "COMPLETED"], allow_null=True)
    total_cost = serializers.FloatField(help_text="Excl VAT", allow_null=True)
    currency = serializers.ChoiceField(choices=["EUR"])
    # Location data
    location = LocationPropertiesSerializer(required=False)
