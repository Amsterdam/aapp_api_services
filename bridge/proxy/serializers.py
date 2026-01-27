from rest_framework import serializers

from core.serializers.address_serializers import AddressSerializer


class WasteGuideRequestSerializer(serializers.Serializer):
    """Serializer for the WasteGuideRequest model."""

    bagNummeraanduidingId = serializers.CharField(required=False)


class AddressSearchRequestSerializer(serializers.Serializer):
    """Serializer for the WasteGuideRequest model."""

    q = serializers.CharField(required=False)
    lat = serializers.FloatField(required=False)
    lon = serializers.FloatField(required=False)


class AddressSearchByNameSerializer(serializers.Serializer):
    """Serializer for the WasteGuideRequest model."""

    query = serializers.CharField()
    street_name = serializers.CharField(required=False)


class AddressSearchByCoordinateSerializer(serializers.Serializer):
    """Serializer for the WasteGuideRequest model."""

    lat = serializers.FloatField()
    lon = serializers.FloatField()


class AddressSearchResponseSerializer(AddressSerializer):
    type = serializers.ChoiceField(choices=["woonplaats", "adres", "weg"])


class AddressPostalAreaResponseSerializer(serializers.Serializer):
    postal_area = serializers.CharField()
