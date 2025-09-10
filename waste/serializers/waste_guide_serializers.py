from django.conf import settings
from rest_framework import serializers

from waste.constants import WASTE_COLLECTION_BY_APPOINTMENT_CODE, WASTE_TYPES_INACTIVE
from waste.models import NotificationSchedule


class WasteRequestSerializer(serializers.Serializer):
    bag_nummeraanduiding_id = serializers.CharField()


class WasteNotificationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSchedule
        fields = "__all__"


class WasteDataSerializer(serializers.Serializer):
    afvalwijzerFractieNaam = serializers.CharField()
    afvalwijzerFractieCode = serializers.ChoiceField(choices=settings.WASTE_CODES)
    afvalwijzerAfvalkalenderFrequentie = serializers.CharField(
        allow_null=True, allow_blank=True
    )
    afvalwijzerAfvalkalenderMelding = serializers.CharField(
        allow_null=True, allow_blank=True
    )
    afvalwijzerAfvalkalenderOpmerking = serializers.CharField(
        allow_null=True, allow_blank=True
    )
    afvalwijzerBuitenzetten = serializers.CharField(allow_null=True, allow_blank=True)
    afvalwijzerBuitenzettenTot = serializers.CharField(
        allow_null=True, allow_blank=True
    )
    afvalwijzerBuitenzettenVanaf = serializers.CharField(
        allow_null=True, allow_blank=True
    )
    afvalwijzerButtontekst = serializers.CharField(allow_null=True, allow_blank=True)
    afvalwijzerInstructie2 = serializers.CharField(allow_null=True, allow_blank=True)
    afvalwijzerOphaaldagen = serializers.CharField(allow_null=True, allow_blank=True)
    afvalwijzerOphaaldagen2Array = serializers.ListField(
        child=serializers.CharField(), allow_null=True, required=False
    )
    afvalwijzerUrl = serializers.CharField(allow_null=True, allow_blank=True)
    afvalwijzerWaar = serializers.CharField(allow_null=True, allow_blank=True)
    afvalwijzerBasisroutetypeCode = serializers.CharField(
        allow_null=True, allow_blank=True
    )
    afvalwijzerFractiecodeActief = serializers.BooleanField(
        allow_null=True, required=False
    )
    gebruiksdoelWoonfunctie = serializers.BooleanField(allow_null=True, required=False)

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)

        def _convert(ext_value):
            data = validated_data.get(ext_value)
            return data if data != "" else None

        internal_data = {
            "label": _convert("afvalwijzerFractieNaam"),
            "code": _convert("afvalwijzerFractieCode"),
            "alert": _convert("afvalwijzerAfvalkalenderMelding"),
            "frequency": _convert("afvalwijzerAfvalkalenderFrequentie"),
            "note": _convert("afvalwijzerAfvalkalenderOpmerking"),
            "button_text": _convert("afvalwijzerButtontekst"),
            "curb_rules": _convert("afvalwijzerBuitenzetten"),
            "curb_rules_from": _convert("afvalwijzerBuitenzettenVanaf"),
            "curb_rules_to": _convert("afvalwijzerBuitenzettenTot"),
            "how": _convert("afvalwijzerInstructie2"),
            "is_collection_by_appointment": validated_data.get(
                "afvalwijzerBasisroutetypeCode"
            )
            == WASTE_COLLECTION_BY_APPOINTMENT_CODE,
            "days": _convert("afvalwijzerOphaaldagen"),
            "days_array": _convert("afvalwijzerOphaaldagen2Array"),
            "url": _convert("afvalwijzerUrl"),
            "where": _convert("afvalwijzerWaar"),
            "active": validated_data.get(
                "afvalwijzerFractiecodeActief",
                validated_data.get("afvalwijzerFractieCode")
                not in WASTE_TYPES_INACTIVE,
            ),
            "is_residential": _convert("gebruiksdoelWoonfunctie"),
        }

        return internal_data


class WasteTypeSerializer(serializers.Serializer):
    label = serializers.CharField()
    code = serializers.ChoiceField(choices=settings.WASTE_CODES)
    curb_rules = serializers.CharField(allow_null=True, default="")
    alert = serializers.CharField(allow_null=True, default="")
    note = serializers.CharField(allow_null=True, default="")
    days_array = serializers.ListField(child=serializers.CharField(), allow_null=True)
    how = serializers.CharField(allow_null=True, default="")
    where = serializers.CharField(allow_null=True, default="")
    button_text = serializers.CharField(allow_null=True, default="")
    url = serializers.CharField(allow_null=True, default="")
    frequency = serializers.CharField(allow_null=True, default="")
    next_date = serializers.DateField(allow_null=True)


class WasteCalendarSerializer(serializers.Serializer):
    date = serializers.DateField()
    label = serializers.CharField()
    code = serializers.ChoiceField(choices=settings.WASTE_CODES)
    curb_rules_from = serializers.CharField(allow_null=True, default="")
    curb_rules_to = serializers.CharField(allow_null=True, default="")
    alert = serializers.CharField(allow_null=True, default="")


class WasteResponseSerializer(serializers.Serializer):
    waste_types = WasteTypeSerializer(many=True)
    calendar = WasteCalendarSerializer(many=True)
    is_residential = serializers.BooleanField()
    is_collection_by_appointment = serializers.BooleanField()
