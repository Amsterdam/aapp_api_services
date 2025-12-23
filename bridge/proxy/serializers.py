import re

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

    lat = serializers.FloatField()
    lon = serializers.FloatField()


class CoordinatesSerializer(serializers.Serializer):
    """Serializer for the Coordinates model."""

    lat = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()

    def _parse_point(self, point):
        if hasattr(point, "coords"):
            lon, lat = point.coords
            return lat, lon
        # string case: "POINT(lon lat)"
        m = re.match(r"POINT\(\s*([-0-9.]+)\s+([-0-9.]+)\s*\)", point)
        if not m:
            return None, None
        lon, lat = m.groups()
        return float(lat), float(lon)

    def get_lat(self, obj) -> float:
        return self._parse_point(obj)[0]

    def get_lon(self, obj) -> float:
        return self._parse_point(obj)[1]


class AddressSearchResponseSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["woonplaats", "adres", "weg"])
    city = serializers.CharField(source="woonplaatsnaam")
    street = serializers.CharField(source="straatnaam")
    coordinates = CoordinatesSerializer(source="centroide_ll")
    bagId = serializers.CharField(required=False, source="nummeraanduiding_id")
    number = serializers.IntegerField(required=False, source="huisnummer")
    additionLetter = serializers.CharField(required=False, source="huisletter")
    additionNumber = serializers.CharField(
        required=False, source="huisnummertoevoeging"
    )
    postcode = serializers.CharField(required=False)


class AddressPostalAreaResponseSerializer(serializers.Serializer):
    postal_area = serializers.CharField()
