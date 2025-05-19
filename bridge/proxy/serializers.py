from rest_framework import serializers


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

    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class AddressSearchResponseSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["adres", "weg"])
    woonplaatsnaam = serializers.CharField()
    centroide_ll = serializers.CharField()
    straatnaam = serializers.CharField()
    # The following fields seem to only be used for results of type 'adres'
    postcode = serializers.CharField(required=False)
    nummeraanduiding_id = serializers.CharField(required=False)
    huisnummer = serializers.IntegerField(required=False)
    huisletter = serializers.CharField(required=False)
    huisnummertoevoeging = serializers.CharField(required=False)
