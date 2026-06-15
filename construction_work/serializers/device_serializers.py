from rest_framework import serializers


class DeleteDeviceDataResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["deleted", "already_absent"])
    message = serializers.CharField()
