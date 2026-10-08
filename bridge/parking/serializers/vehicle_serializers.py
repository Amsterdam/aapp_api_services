from rest_framework import serializers


class VehicleInformationRequestSerializer(serializers.Serializer):
    licence_plate = serializers.CharField()


class VehicleInformationContentSerializer(serializers.Serializer):
    brand = serializers.CharField()
    type = serializers.CharField()
    color = serializers.CharField()


class VehicleInformationResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    content = VehicleInformationContentSerializer(allow_null=True)
