from rest_framework import serializers

from core.serializers.address_serializers import AddressSerializer

OPERATION_STATE_CHOICES = ["OPERATIVE", "INOPERATIVE", "OFFLINE", "UNKNOWN"]


class OpeningTimesSerializer(serializers.Serializer):
    regular_hours = serializers.ListField(child=serializers.IntegerField())
    twentyfourseven = serializers.BooleanField()
    exceptional_openings = serializers.ListField(child=serializers.IntegerField())
    exceptional_closings = serializers.ListField(child=serializers.IntegerField())


class LocationResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    address = AddressSerializer()
    opening_times = OpeningTimesSerializer()
    # available_sockets = serializers.IntegerField()
    total_sockets = serializers.IntegerField()


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
    ocpp_evse_id = serializers.IntegerField()
    evse_id = serializers.CharField()
    status = serializers.ChoiceField(choices=OPERATION_STATE_CHOICES)
    connectors = serializers.ListField(child=ConnectorSerializer())


class ChargingStationSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.ChoiceField(choices=OPERATION_STATE_CHOICES)
    location_id = serializers.CharField()
    evses = serializers.ListField(child=EVSESerializer())


class LocationDetailResponseSerializer(LocationResponseSerializer):
    tariff = TariffSerializer()
    charging_stations = serializers.ListField(child=ChargingStationSerializer())
