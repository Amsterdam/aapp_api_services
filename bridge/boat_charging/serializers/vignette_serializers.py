from rest_framework import serializers


class VignettesListResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    vignet_number = serializers.CharField()
    boat_name = serializers.CharField()
    created_at = serializers.CharField()


class VignettesLinkRequestSerializer(serializers.Serializer):
    vignet_number = serializers.CharField()
    boat_name = serializers.CharField(required=False)
    postal_code = serializers.CharField()


class VerifyVignetteRequestSerializer(serializers.Serializer):
    vignet_number = serializers.CharField()
    postal_code = serializers.CharField()


class VerifyVignetteResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    expiration_date = serializers.CharField()
