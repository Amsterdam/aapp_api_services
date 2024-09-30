from rest_framework import serializers

from contact.models import CityOffice, OpeningHours, OpeningHoursException


class OpeningTimeSerializer(serializers.Serializer):
    hours = serializers.IntegerField()
    minutes = serializers.IntegerField()


class RegularOpeningHoursSerializer(serializers.ModelSerializer):
    opening = serializers.SerializerMethodField()
    closing = serializers.SerializerMethodField()

    class Meta:
        model = OpeningHours
        fields = ("day_of_week", "opening", "closing")

    def get_opening(self, obj):
        return {"hours": obj.opens_hours, "minutes": obj.opens_minutes}

    def get_closing(self, obj):
        return {"hours": obj.closes_hours, "minutes": obj.closes_minutes}


class ExceptionOpeningHoursSerializer(serializers.ModelSerializer):
    opening = serializers.SerializerMethodField()
    closing = serializers.SerializerMethodField()

    class Meta:
        model = OpeningHoursException
        fields = ("date", "opening", "closing")

    def get_opening(self, obj):
        if obj.opens_hours is not None:
            return {"hours": obj.opens_hours, "minutes": obj.opens_minutes}
        return None

    def get_closing(self, obj):
        if obj.closes_hours is not None:
            return {"hours": obj.closes_hours, "minutes": obj.closes_minutes}
        return None


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
    directionsUrl = serializers.CharField(source="directions_url", allow_null=True)
    visitingHoursContent = serializers.CharField(
        source="visiting_hours_content", allow_null=True
    )
    images = serializers.JSONField()
    appointment = serializers.JSONField()

    class Meta:
        model = CityOffice
        fields = (
            "identifier",
            "title",
            "images",
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
