from rest_framework import serializers


class VignettesListResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    vignet_number = serializers.CharField()
    boat_name = serializers.CharField()
    created_at = serializers.CharField()


class VignettesLinkRequestSerializer(serializers.Serializer):
    vignet_number = serializers.CharField()
    boat_name = serializers.CharField()
