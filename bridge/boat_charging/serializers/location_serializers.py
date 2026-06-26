from rest_framework import serializers

from core.serializers.address_serializers import AddressSerializer

OPERATION_STATE_CHOICES = ["OPERATIVE", "INOPERATIVE", "OFFLINE", "UNKNOWN", "OCCUPIED"]

OPERATION_STATE_MAPPING = {
    "OPERATIVE": "OPERATIVE",
    "INOPERATIVE": "INOPERATIVE",
    "OFFLINE": "OFFLINE",
    "UNKNOWN": "UNKNOWN",
    "OCCUPIED": "OCCUPIED",
    "FAULTED": "INOPERATIVE",
    "AVAILABLE": "OPERATIVE",
    "CHARGING": "OCCUPIED",
    "RESERVED": "OCCUPIED",
}


class HourMinuteField(serializers.Serializer):
    hours = serializers.IntegerField()
    minutes = serializers.IntegerField()


class RegularOpeningHoursSerializer(serializers.Serializer):
    dayOfWeek = serializers.IntegerField()
    opening = HourMinuteField()
    closing = HourMinuteField()


class OpeningTimesSerializer(serializers.Serializer):
    regular_hours = RegularOpeningHoursSerializer(many=True, allow_empty=True)
    twentyfourseven = serializers.BooleanField()


class PointGeometrySerializer(serializers.Serializer):
    type = serializers.CharField(default="Point", read_only=True)
    coordinates = serializers.ListField(child=serializers.FloatField())


class LocationPropertiesSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    address = AddressSerializer()
    opening_times = OpeningTimesSerializer()
    available_sockets = serializers.IntegerField()
    total_sockets = serializers.IntegerField()
    status = serializers.ChoiceField(choices=OPERATION_STATE_CHOICES, required=False)
    max_kw = serializers.FloatField(required=False, allow_null=True)


class LocationListItemSerializer(serializers.Serializer):
    type = serializers.CharField(default="Feature", read_only=True)
    geometry = PointGeometrySerializer()
    properties = LocationPropertiesSerializer()


class LocationListResponseSerializer(serializers.Serializer):
    type = serializers.CharField(default="FeatureCollection", read_only=True)
    features = LocationListItemSerializer(many=True)


class TariffSerializer(serializers.Serializer):
    id = serializers.CharField()
    energy_price_per_kwh = serializers.FloatField()
    charging_time_price_per_hour = serializers.FloatField()
    parking_time_price_per_hour = serializers.FloatField()
    flat_fee_price = serializers.FloatField()


class ConnectorSerializer(serializers.Serializer):
    connector_id = serializers.IntegerField()
    max_amp = serializers.IntegerField()
    voltage = serializers.IntegerField()
    # max_electric_powers = serializers.IntegerField()
    status = serializers.ChoiceField(choices=OPERATION_STATE_CHOICES)


class EVSESerializer(serializers.Serializer):
    id = serializers.CharField()
    display_name = serializers.CharField()
    ocpp_evse_id = serializers.IntegerField()
    evse_id = serializers.CharField()
    status = serializers.ChoiceField(choices=OPERATION_STATE_CHOICES)
    connectors = serializers.ListField(child=ConnectorSerializer())


class ChargingStationSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.ChoiceField(choices=OPERATION_STATE_CHOICES)
    location_id = serializers.CharField()
    evses = serializers.ListField(child=EVSESerializer())


class LocationDetailResponseSerializer(LocationPropertiesSerializer):
    tariff = TariffSerializer(allow_null=True)
    charging_stations = serializers.ListField(child=ChargingStationSerializer())
