from rest_framework import serializers


class GuestLoginResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    expires_in = serializers.IntegerField()
    token_type = serializers.CharField()


class OIDCSettingsResponseSerializer(serializers.Serializer):
    user_pool_id = serializers.CharField()
    client_id = serializers.CharField()
    issuer = serializers.URLField()
    redirect_url = serializers.URLField()
    scopes = serializers.ListField(child=serializers.CharField())
    pkce_required = serializers.BooleanField()
