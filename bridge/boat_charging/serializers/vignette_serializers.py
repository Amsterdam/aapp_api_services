from rest_framework import serializers


class RequiredVignetteFieldSerializer(serializers.Serializer):
    vignette_number = serializers.CharField()
    postal_code = serializers.CharField()


class VignettesResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    vignette_number = serializers.CharField()
    boat_name = serializers.CharField(required=False, allow_null=True)
    created_at = serializers.CharField()


class VignettesLinkRequestSerializer(RequiredVignetteFieldSerializer):
    boat_name = serializers.CharField(required=False)


class VerifyVignetteResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    expiration_date = serializers.CharField()
