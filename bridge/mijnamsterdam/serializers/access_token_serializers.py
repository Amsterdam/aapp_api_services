from rest_framework import serializers


class AccessTokenRequestSerializer(serializers.Serializer):
    authorization_code = serializers.CharField()
    code_verifier = serializers.CharField()


class SessionSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.CharField()
    expiry = serializers.DateTimeField()


class AccessTokenResponseSerializer(serializers.Serializer):
    session = SessionSerializer()
