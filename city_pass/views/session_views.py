from typing import Tuple

from django.conf import settings
from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response

from city_pass import authentication, models
from city_pass.exceptions import TokenExpiredException, TokenInvalidException
from city_pass.serializers import session_serializers as serializers
from city_pass.views.extend_schema import extend_schema_with_access_token
from core.utils.openapi_utils import extend_schema_for_api_key
from core.views.mixins import DeviceIdMixin


class SessionInitView(DeviceIdMixin, generics.CreateAPIView):
    serializer_class = serializers.SessionTokensOutSerializer
    device_id_required = False

    @extend_schema_for_api_key(
        success_response=serializers.SessionTokensOutSerializer,
        request=None,
        additional_params=[
            OpenApiParameter(
                settings.HEADER_DEVICE_ID,
                OpenApiTypes.STR,
                OpenApiParameter.HEADER,
                required=False,
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        """Initialize a new session and return access and refresh token pair.
        The device_id is optional and used to send notifications to the user."""
        access_token, refresh_token = self.init_session()
        serializer = self.get_serializer((access_token, refresh_token))
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def init_session(self) -> Tuple[models.AccessToken, models.RefreshToken]:
        """Initialize a new session with related access and refresh token.

        Returns:
            Tuple[models.AccessToken, models.RefreshToken]: a new token pair
        """
        if self.device_id:
            old_sessions = models.Session.objects.filter(device_id=self.device_id).all()
            old_sessions.delete()  # Remove old sessions for this device_id

        new_session = models.Session(device_id=self.device_id)
        new_session.save()

        access_token = models.AccessToken(session=new_session)
        access_token.save()

        refresh_token = models.RefreshToken(session=new_session)
        refresh_token.save()

        return access_token, refresh_token


class SessionPostCredentialView(generics.CreateAPIView):
    serializer_class = serializers.SessionCredentialInSerializer
    authentication_classes = [authentication.SessionCredentialsKeyAuthentication]

    @extend_schema_for_api_key(
        success_response=serializers.DetailResultSerializer,
        exceptions=[TokenInvalidException, TokenExpiredException],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        access_token = models.AccessToken.objects.filter(
            token=validated_data["session_token"]
        ).first()
        if not access_token:
            raise TokenInvalidException()

        access_token.is_valid()

        access_token.session.encrypted_adminstration_no = validated_data[
            "encrypted_administration_no"
        ]
        access_token.session.save()

        return Response(data=detail_message("Success"), status=status.HTTP_200_OK)


class SessionRefreshAccessView(generics.CreateAPIView):
    serializer_class = serializers.SessionRefreshInSerializer

    @extend_schema_for_api_key(
        success_response=serializers.SessionTokensOutSerializer,
        exceptions=[TokenInvalidException, TokenExpiredException],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        refresh_token = models.RefreshToken.objects.filter(
            token=validated_data["refresh_token"]
        ).first()
        if not refresh_token:
            raise TokenInvalidException()

        refresh_token.is_valid()

        new_access_token, new_refresh_token = self.refresh_tokens(refresh_token)
        serializer = serializers.SessionTokensOutSerializer(
            (new_access_token, new_refresh_token)
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def refresh_tokens(
        self, incoming_refresh_token: models.RefreshToken
    ) -> Tuple[models.AccessToken, models.RefreshToken]:
        """Create a new access en refresh token pair.
        An incoming refresh token does not get invalidated immediatly,
        in order to allow a client to retry a refresh request in case they did not receive the result.
        All other refresh tokens related to the session get removed, should always be max 1 token.
        The existing access token gets removed.
        New refresh and access token get generated and returned.

        Wrapped in an automic transaction so if something goes wrong in the database, it can be fully reverted.

        Args:
            incoming_refresh_token (models.RefreshToken): token to set expiration and get related session from

        Returns:
            Tuple[str, str]: a new token pair in string format
        """
        session: models.Session = incoming_refresh_token.session

        # Incoming refresh token will stay valid for a little longer, so client can retry the request
        incoming_refresh_token.expire()

        # Any remaining refresh tokens get removed
        for rt in session.refreshtoken_set.all():
            if rt == incoming_refresh_token:
                continue
            rt.delete()

        # Create a new refresh token
        new_refresh_token = models.RefreshToken.objects.create(session=session)

        # Remove the existing access token
        session.accesstoken.delete()
        # Then create a new access token
        new_access_token = models.AccessToken.objects.create(session=session)

        return new_access_token, new_refresh_token


class SessionLogoutView(generics.CreateAPIView):
    serializer_class = serializers.DetailResultSerializer
    authentication_classes = [authentication.AccessTokenAuthentication]

    @extend_schema_with_access_token(
        success_response=serializers.DetailResultSerializer,
        request=None,
    )
    def post(self, request, *args, **kwargs):
        session = request.user
        session.delete()
        return Response(data=detail_message("Success"), status=status.HTTP_200_OK)


def detail_message(detail: str):
    return {"detail": detail}
