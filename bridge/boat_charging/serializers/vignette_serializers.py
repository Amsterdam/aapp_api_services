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
    expiration_date = serializers.CharField(required=False)
    reason = serializers.CharField(required=False)

    def validate(self, attrs):
        status = attrs.get("status")

        if status.lower() == "valid" and not attrs.get("expiration_date"):
            raise serializers.ValidationError(
                {"expiration_date": "This field is required when status is valid."}
            )

        if status.lower() != "valid" and not attrs.get("reason"):
            raise serializers.ValidationError(
                {"reason": "This field is required when status is not valid."}
            )

        return attrs
