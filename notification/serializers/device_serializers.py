from rest_framework import serializers

from notification.models import Device


class DeviceRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = "__all__"
        extra_kwargs = {
            "os": {"required": True, "allow_blank": False},
            "firebase_token": {"required": True, "allow_blank": False},
        }


class DeviceRegisterPostSwaggerSerializer(serializers.Serializer):
    firebase_token = serializers.CharField()
    os = serializers.CharField()
