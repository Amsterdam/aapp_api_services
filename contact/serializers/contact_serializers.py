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
    image = serializers.JSONField(allow_null=False)
    address = AddressSerializer(allow_null=False)
    addressContent = serializers.JSONField(allow_null=False)
    coordinates = CoordinatesSerializer(allow_null=False)
    directionsUrl = serializers.URLField(allow_null=False)
    appointment = serializers.JSONField(allow_null=False)
    visitingHoursContent = serializers.CharField(allow_null=False)
    visitingHours = OpeningHoursSerializer()
    order = serializers.IntegerField(allow_null=False)


class CityOfficeResultSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    result = CityOfficeOutSerializer(many=True)


class WaitingTimeOutSerializer(serializers.Serializer):
    title = serializers.CharField()
    identifier = serializers.CharField()
    queued = serializers.IntegerField()
    waitingTime = serializers.IntegerField()


class WaitingTimeResultSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    result = WaitingTimeOutSerializer(many=True)
