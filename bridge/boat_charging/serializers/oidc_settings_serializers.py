from rest_framework import serializers


class OIDCSettingsResponseSerializer(serializers.Serializer):
    issuer = serializers.CharField()
    discovery_url = serializers.CharField()
    client_id = serializers.CharField()
    redirect_uri = serializers.CharField()
    scopes = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
    )
    response_type = serializers.CharField()
    pkce_required = serializers.BooleanField()
