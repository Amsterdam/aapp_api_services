from rest_framework import serializers

from notification.models import Client


class ClientRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"
        extra_kwargs = {
            "os": {"required": True, "allow_blank": False},
            "firebase_token": {"required": True, "allow_blank": False},
        }


class ClientRegisterPostSwaggerSerializer(serializers.Serializer):
    firebase_token = serializers.CharField()
    os = serializers.CharField()
