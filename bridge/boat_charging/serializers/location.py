from rest_framework import serializers

from core.serializers.address_serializers import AddressSerializer


class TariffSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    energy_price_per_kwh = serializers.FloatField()
    charging_time_price_per_hour = serializers.FloatField()
    parking_time_price_per_hour = serializers.FloatField()
    flat_free_price = serializers.FloatField()


class LocationResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    address = AddressSerializer()
    opening_times = serializers.CharField()
    charging_station_ids = serializers.ListField(child=serializers.CharField())
    tariff = TariffSerializer()
    available_sockets = serializers.IntegerField()
    total_sockets = serializers.IntegerField()
