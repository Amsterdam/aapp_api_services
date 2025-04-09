from rest_framework import serializers


class WasteGuideRequestSerializer(serializers.Serializer):
    """Serializer for the WasteGuideRequest model."""

    bagNummeraanduidingId = serializers.CharField(required=False)


class AddressSearchRequestSerializer(serializers.Serializer):
    """Serializer for the WasteGuideRequest model."""

    q = serializers.CharField()
