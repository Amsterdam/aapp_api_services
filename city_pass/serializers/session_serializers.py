from datetime import datetime, timedelta

from django.conf import settings
from rest_framework import serializers

from city_pass.models import AccessToken, RefreshToken, SessionToken
from city_pass.utils import get_token_cut_off


class DetailResultSerializer(serializers.Serializer):
    detail = serializers.CharField(default="Success")


class SessionTokensOutSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    access_token_expiration = serializers.DateTimeField()
    refresh_token = serializers.CharField()
    refresh_token_expiration = serializers.DateTimeField()

    def _get_expiration_datetime(self, token: SessionToken) -> datetime:
        token_ttl = None
        if isinstance(token, AccessToken):
            token_ttl = settings.TOKEN_TTLS["ACCESS_TOKEN"]
        elif isinstance(token, RefreshToken):
            token_ttl = settings.TOKEN_TTLS["REFRESH_TOKEN"]

        exp_date_ttl_based = token.created_at + timedelta(seconds=token_ttl)
        exp_date_cut_off_based = get_token_cut_off()

        # Return the earliest date
        return min(exp_date_ttl_based, exp_date_cut_off_based)

    def to_representation(self, instance):
        """
        Convert the input instance (which should be a tuple of (access_token, refresh_token))
        into the serialized representation.
        """
        access_token, refresh_token = instance

        return {
            "access_token": access_token.token,
            "access_token_expiration": self._get_expiration_datetime(access_token),
            "refresh_token": refresh_token.token,
            "refresh_token_expiration": self._get_expiration_datetime(refresh_token),
        }


class SessionCredentialInSerializer(serializers.Serializer):
    session_token = serializers.CharField(required=True)
    encrypted_administration_no = serializers.CharField(required=True)


class SessionRefreshInSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)
