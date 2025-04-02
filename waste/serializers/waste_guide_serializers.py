from django.conf import settings
from rest_framework import serializers

from waste.models import NotificationSchedule


class WasteRequestSerializer(serializers.Serializer):
    bag_nummeraanduiding_id = serializers.CharField()


class WasteNotificationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSchedule
        fields = "__all__"


class WasteDataSerializer(serializers.Serializer):
    afvalwijzerFractieNaam = serializers.CharField()
    afvalwijzerFractieCode = serializers.ChoiceField(choices=settings.WASTE_TYPES)
    afvalwijzerBuitenzettenVanaf = serializers.CharField(
        allow_null=True, allow_blank=True
    )
    afvalwijzerBuitenzettenTot = serializers.CharField(
        allow_null=True, allow_blank=True
    )
    afvalwijzerOphaaldagen = serializers.CharField(allow_null=True, allow_blank=True)
    afvalwijzerAfvalkalenderMelding = serializers.CharField(
        allow_null=True, allow_blank=True
    )
    afvalwijzerAfvalkalenderOpmerking = serializers.CharField(
        allow_null=True, allow_blank=True
    )
    afvalwijzerInstructie2 = serializers.CharField(allow_null=True, allow_blank=True)
    afvalwijzerAfvalkalenderFrequentie = serializers.CharField(
        allow_null=True, allow_blank=True
    )


class WasteCalendarSerializer(serializers.Serializer):
    date = serializers.DateField()
    label = serializers.CharField()
    type = serializers.ChoiceField(choices=settings.WASTE_TYPES)
    curb_rules_from = serializers.CharField(allow_null=True)
    curb_rules_to = serializers.CharField(allow_null=True)
    note = serializers.CharField(allow_null=True)


class WasteTypeSerializer(serializers.Serializer):
    label = serializers.CharField()
    type = serializers.ChoiceField(choices=settings.WASTE_TYPES)
    curb_rules_from = serializers.CharField(allow_null=True)
    curb_rules_to = serializers.CharField(allow_null=True)
    note = serializers.CharField(allow_null=True)
    instruction = serializers.CharField(allow_null=True)
    next_date = serializers.DateField(allow_null=True)


class WasteResponseSerializer(serializers.Serializer):
    waste_types = WasteTypeSerializer(many=True)
    calendar = WasteCalendarSerializer(many=True)
