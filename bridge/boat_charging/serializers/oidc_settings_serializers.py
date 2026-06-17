from rest_framework import serializers


class OIDCSettingsResponseSerializer(serializers.Serializer):
    cognito_user_pool_id = serializers.CharField()
    cognito_user_pool_client_id = serializers.CharField()
    pkce_required = serializers.BooleanField()
