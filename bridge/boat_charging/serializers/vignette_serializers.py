from rest_framework import serializers

KNOWN_VIGNETTE_REASONS = (
    "NOT_FOUND",
    "MISMATCH",
    "CANCELLED",
    "EXPIRED",
    "ONLY_ENVIRONMENT_TYPE_ALLOWED",
    "UNKNOWN",
)


class VignetteReasonField(serializers.ChoiceField):
    def to_internal_value(self, data):
        if not isinstance(data, str) or data not in KNOWN_VIGNETTE_REASONS:
            data = "UNKNOWN"
        return super().to_internal_value(data)


class RequiredVignetteFieldSerializer(serializers.Serializer):
    vignette_number = serializers.CharField()
    postal_code = serializers.CharField()


class VignettesResponseSerializer(RequiredVignetteFieldSerializer):
    id = serializers.IntegerField()
    boat_name = serializers.CharField(required=False, allow_null=True)
    expiration_date = serializers.CharField()


class VerifyVignetteResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    expiration_date = serializers.CharField(required=False)
    reason = VignetteReasonField(choices=KNOWN_VIGNETTE_REASONS, required=False)

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
