from rest_framework import serializers

from notification.models import Device, WasteDevice


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


class WasteDeviceRequestSerializer(serializers.ModelSerializer):
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = WasteDevice
        fields = ["bag_nummeraanduiding_id", "updated_at"]

    def create(self, validated_data):
        device_id = self.context.get("device_id")
        if not device_id:
            raise serializers.ValidationError("Device ID header missing")

        return WasteDevice.objects.create(
            device_id=device_id,
            **validated_data,
        )


class WasteDeviceResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField(required=False)
