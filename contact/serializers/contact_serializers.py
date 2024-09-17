from rest_framework import serializers


class OpeningTimeSerializer(serializers.Serializer):
    hours = serializers.IntegerField()
    minutes = serializers.IntegerField()


class RegularOpeningHoursSerializer(serializers.Serializer):
    dayOfWeek = serializers.IntegerField()
    opening = OpeningTimeSerializer()
    closing = OpeningTimeSerializer()


class ExceptionOpeningHoursSerializer(serializers.Serializer):
    date = serializers.DateField()
    opening = OpeningTimeSerializer()
    closing = OpeningTimeSerializer()


class OpeningHoursSerializer(serializers.Serializer):
    regular = RegularOpeningHoursSerializer(many=True)
    exceptions = ExceptionOpeningHoursSerializer(many=True)


class AddressSerializer(serializers.Serializer):
    streetName = serializers.CharField()
    streetNumber = serializers.CharField()
    postalCode = serializers.CharField()
    city = serializers.CharField()


class CoordinatesSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class CityOfficeOutSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    title = serializers.CharField()
    image = serializers.JSONField()
    address = AddressSerializer()
    addressContent = serializers.JSONField()
    coordinates = CoordinatesSerializer()
    directionsUrl = serializers.URLField()
    appointment = serializers.JSONField()
    visitingHoursContent = serializers.CharField()
    visitingHours = OpeningHoursSerializer()
    order = serializers.IntegerField()


class CityOfficeResultSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    result = CityOfficeOutSerializer()


class WaitingTimeOutSerializer(serializers.Serializer):
    title = serializers.CharField()
    identifier = serializers.CharField()
    queued = serializers.IntegerField()
    waitingTime = serializers.IntegerField()


class WaitingTimeResultSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    result = WaitingTimeOutSerializer()
