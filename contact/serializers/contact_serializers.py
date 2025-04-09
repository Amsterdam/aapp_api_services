from rest_framework import serializers

from contact.models import CityOffice, OpeningHours, OpeningHoursException


class TimeDictField(serializers.Field):
    def to_representation(self, value):
        if value is None:
            return None
        return {"hours": value.hour, "minutes": value.minute}


class RegularOpeningHoursSerializer(serializers.ModelSerializer):
    opening = TimeDictField(source="opens_time")
    closing = TimeDictField(source="closes_time")
    dayOfWeek = serializers.JSONField(source="day_of_week")

    class Meta:
        model = OpeningHours
        fields = ("dayOfWeek", "opening", "closing")


class ExceptionOpeningHoursSerializer(serializers.ModelSerializer):
    opening = TimeDictField(source="opens_time")
    closing = TimeDictField(source="closes_time")

    class Meta:
        model = OpeningHoursException
        fields = ("date", "opening", "closing")


class OpeningHoursSerializer(serializers.Serializer):
    regular = RegularOpeningHoursSerializer(many=True)
    exceptions = ExceptionOpeningHoursSerializer(many=True)


class AddressSerializer(serializers.Serializer):
    streetName = serializers.CharField(source="street_name")
    streetNumber = serializers.CharField(source="street_number")
    postalCode = serializers.CharField(source="postal_code")
    city = serializers.CharField()


class CoordinatesSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class CityOfficeSerializer(serializers.ModelSerializer):
    address = AddressSerializer(source="*")
    coordinates = CoordinatesSerializer(source="*")
    visitingHours = serializers.SerializerMethodField()
    addressContent = serializers.JSONField(source="address_content", allow_null=True)
    directionsUrl = serializers.CharField(source="directions_url")
    visitingHoursContent = serializers.CharField(
        source="visiting_hours_content", allow_null=True
    )
    image = serializers.JSONField(source="images")
    appointment = serializers.JSONField()

    class Meta:
        model = CityOffice
        fields = (
            "identifier",
            "title",
            "image",
            "address",
            "addressContent",
            "coordinates",
            "directionsUrl",
            "appointment",
            "visitingHoursContent",
            "visitingHours",
            "order",
        )

    def get_visitingHours(self, obj):
        regular = RegularOpeningHoursSerializer(
            obj.openinghours_set.all(), many=True
        ).data
        exceptions = ExceptionOpeningHoursSerializer(
            obj.openinghoursexception_set.all(), many=True
        ).data
        return {"regular": regular, "exceptions": exceptions}


class CityOfficeResultSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    result = CityOfficeSerializer(many=True)
