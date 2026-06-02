from rest_framework import serializers


class DeviceResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["OK", "ERROR"])
    profile_name = serializers.CharField(required=False)


class LogoutNotificationRequestSerializer(serializers.Serializer):
    device_ids = serializers.ListField(child=serializers.CharField())

    def validate_device_ids(self, value: list[str]) -> list[str]:
        # Keep order while removing duplicates.
        return list(dict.fromkeys(value))
