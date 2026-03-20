from rest_framework import serializers


class WasteRequestSerializer(serializers.Serializer):
    bag_nummeraanduiding_id = serializers.CharField()
