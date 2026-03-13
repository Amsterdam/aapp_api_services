from rest_framework import serializers

from notification.models import Device, WasteNotification


class DeviceRegisterRequestSerializer(serializers.Serializer):
    firebase_token = serializers.CharField()
    os = serializers.CharField()


class DeviceRegisterResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = "__all__"
        extra_kwargs = {
            "os": {"required": True, "allow_blank": False},
            "firebase_token": {"required": True, "allow_blank": False},
        }


class WasteRequestSerializer(serializers.Serializer):
    bag_nummeraanduiding_id = serializers.CharField()


class WasteNotificationSerializer(serializers.ModelSerializer):
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = WasteNotification
        fields = ["bag_nummeraanduiding_id", "updated_at"]

    def create(self, validated_data):
        device_id = self.context.get("device_id")
        if not device_id:
            raise serializers.ValidationError("Device ID header missing")

        return WasteNotification.objects.create(
            device_id=device_id,
            **validated_data,
        )
