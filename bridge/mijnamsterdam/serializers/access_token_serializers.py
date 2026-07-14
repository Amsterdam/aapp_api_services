from rest_framework import serializers


class AccessTokenRequestSerializer(serializers.Serializer):
    authorization_code = serializers.CharField()
    code_verifier = serializers.CharField()


class AccessTokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
