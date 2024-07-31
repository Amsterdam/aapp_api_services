from rest_framework import serializers


class SessionTokensOutSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()


class SessionCredentialInSerializer(serializers.Serializer):
    session_token = serializers.CharField(required=True)
    encrypted_administration_no = serializers.CharField(required=True)


class SessionResultSerializer(serializers.Serializer):
    detail = serializers.CharField()


class SessionRefreshInSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)


class MijnAmsDataSerializer(serializers.Serializer):
    pass
