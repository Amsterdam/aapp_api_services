from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from core.serializers.address_serializers import AddressSerializer
from waste.models import OpeningHoursException, RecycleLocation, RegularOpeningHours


class TimeDictField(serializers.Field):
    def to_representation(self, value):
        if value is None:
            return None
        return {"hours": value.hour, "minutes": value.minute}


class RegularOpeningHoursSerializer(serializers.ModelSerializer):
    opening = TimeDictField(source="opens_time")
    closing = TimeDictField(source="closes_time")
    dayOfWeek = serializers.IntegerField(source="day_of_week")

    class Meta:
        model = RegularOpeningHours
        fields = ["dayOfWeek", "opening", "closing"]


class ExceptionOpeningHoursSerializer(serializers.ModelSerializer):
    opening = TimeDictField(source="opens_time")
    closing = TimeDictField(source="closes_time")

    class Meta:
        model = OpeningHoursException
        fields = ["date", "opening", "closing", "description"]


class OpeningHoursSerializer(serializers.Serializer):
    regular = RegularOpeningHoursSerializer(many=True)
    exceptions = ExceptionOpeningHoursSerializer(many=True)


class RecycleLocationResponseSerializer(serializers.ModelSerializer):
    address = AddressSerializer(source="*")
    openingHours = serializers.SerializerMethodField()
    commercialWaste = serializers.BooleanField(source="commercial_waste")

    class Meta:
        model = RecycleLocation
        fields = ["id", "name", "address", "openingHours", "commercialWaste"]

    @extend_schema_field(OpeningHoursSerializer)
    def get_openingHours(self, obj):
        regular_hours = RegularOpeningHours.objects.filter(
            recycle_location_opening_hours__recycle_location=obj.get("id")
        ).filter(opens_time__isnull=False, closes_time__isnull=False)

        exceptions = OpeningHoursException.objects.filter(
            affected_locations=obj.get("id")
        )

        opening_hours = OpeningHoursSerializer(
            {"regular": regular_hours, "exceptions": exceptions}
        )
        return opening_hours.data
