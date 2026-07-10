from rest_framework import serializers


class LogoutNotificationRequestSerializer(serializers.Serializer):
    device_ids = serializers.ListField(child=serializers.CharField(max_length=1000))

    def validate_device_ids(self, value: list[str]) -> list[str]:
        # Keep order while removing duplicates.
        return list(dict.fromkeys(value))


class LogoutNotificationResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["OK", "ERROR"])
