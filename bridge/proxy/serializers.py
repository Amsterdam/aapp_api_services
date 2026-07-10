from rest_framework import serializers

from core.serializers.address_serializers import AddressSerializer


class AddressSearchRequestSerializer(serializers.Serializer):
    q = serializers.CharField(required=False)
    lat = serializers.FloatField(required=False)
    lon = serializers.FloatField(required=False)


class AddressSearchByNameSerializer(serializers.Serializer):
    query = serializers.CharField()
    street_name = serializers.CharField(required=False)


class AddressSearchByCoordinateSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class AddressSearchResponseSerializer(AddressSerializer):
    type = serializers.ChoiceField(choices=["woonplaats", "adres", "weg"])


class AddressPostalAreaResponseSerializer(serializers.Serializer):
    postal_area = serializers.CharField()
