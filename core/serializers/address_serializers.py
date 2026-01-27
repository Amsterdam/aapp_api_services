from rest_framework import serializers


class CoordinatesSerializer(serializers.Serializer):
    lat = serializers.CharField()
    lon = serializers.CharField()


class AddressSerializer(serializers.Serializer):
    city = serializers.CharField()
    street = serializers.CharField()
    coordinates = CoordinatesSerializer(source="*")
    cityDistrict = serializers.CharField(required=False)
    bagId = serializers.CharField(required=False)
    number = serializers.CharField(required=False)
    additionLetter = serializers.CharField(required=False)
    additionNumber = serializers.CharField(required=False)
    postcode = serializers.CharField(required=False)
