from rest_framework import serializers


class DeviceResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["OK", "ERROR"])
    profile_name = serializers.CharField(required=False)
