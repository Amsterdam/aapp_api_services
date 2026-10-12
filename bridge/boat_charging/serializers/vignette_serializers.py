from rest_framework import serializers


class RequiredVignetteFieldSerializer(serializers.Serializer):
    vignette_number = serializers.CharField()
    postal_code = serializers.CharField()


class VignettesResponseSerializer(RequiredVignetteFieldSerializer):
    id = serializers.IntegerField()
    boat_name = serializers.CharField(required=False, allow_null=True)
    created_at = serializers.CharField()


class VerifyVignetteResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    expiration_date = serializers.CharField()
