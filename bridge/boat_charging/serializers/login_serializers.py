from rest_framework import serializers


class GuestLoginResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    expires_in = serializers.IntegerField()
    token_type = serializers.CharField()
