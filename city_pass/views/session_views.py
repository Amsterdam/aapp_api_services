from typing import Tuple

from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from city_pass import models, serializers, authentication
from city_pass.utils import detail_message
from city_pass.views.extend_schema import extend_schema


class SessionInitView(generics.RetrieveAPIView):
    serializer_class = serializers.SessionTokensOutSerializer

    @extend_schema(success_response=serializers.SessionTokensOutSerializer, error_response_codes=[403])
    def get(self, request, *args, **kwargs):
        access_token_str, refresh_token_str = self.init_session()
        serializer = self.get_serializer(
            {"access_token": access_token_str, "refresh_token": refresh_token_str}
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def init_session(self) -> Tuple[str, str]:
        """Initialize a new session with related access and refresh token.

        Returns:
            Tuple[str, str]: a new token pair in string format
        """

        new_session = models.Session()
        new_session.save()

        access_token = models.AccessToken(session=new_session)
        access_token.save()

        refresh_token = models.RefreshToken(session=new_session)
        refresh_token.save()

        return access_token.token, refresh_token.token


class SessionPostCredentialView(generics.CreateAPIView):
    serializer_class = serializers.SessionCredentialInSerializer

    @extend_schema(success_response=serializers.DetailResultSerializer, error_response_codes=[401, 403])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        access_token = models.AccessToken.objects.filter(
            token=validated_data["session_token"]
        ).first()
        if not access_token:
            return Response(
                data=detail_message("Session token is invalid"),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not access_token.is_valid():
            return Response(
                data=detail_message("Session token has expired"),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token.session.encrypted_adminstration_no = validated_data[
            "encrypted_administration_no"
        ]
        access_token.session.save()

        return Response(data=detail_message("Success"), status=status.HTTP_200_OK)


class SessionRefreshAccessView(generics.CreateAPIView):
    serializer_class = serializers.SessionRefreshInSerializer

    @extend_schema(success_response=serializers.SessionTokensOutSerializer, error_response_codes=[401, 403])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        refresh_token = models.RefreshToken.objects.filter(
            token=validated_data["refresh_token"]
        ).first()
        if not refresh_token:
            return Response(
                data=detail_message("Refresh token is invalid"),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not refresh_token.is_valid():
            return Response(
                data=detail_message("Refresh token has expired"),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token_str, refresh_token_str = self.refresh_tokens(refresh_token)
        serializer = serializers.SessionTokensOutSerializer(
            {"access_token": access_token_str, "refresh_token": refresh_token_str}
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def refresh_tokens(
        self, incoming_refresh_token: models.RefreshToken
    ) -> Tuple[str, str]:
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

        incoming_refresh_token.expire()

        for rt in session.refreshtoken_set.all():
            if rt == incoming_refresh_token:
                continue
            rt.delete()

        new_refresh_token = models.RefreshToken(session=session)
        new_refresh_token.save()

        access_token: models.AccessToken = session.accesstoken
        access_token.delete()

        new_access_token = models.AccessToken(session=session)
        new_access_token.save()

        return new_access_token.token, new_refresh_token.token


class SessionLogoutView(generics.CreateAPIView):
    @extend_schema(success_response=serializers.DetailResultSerializer,error_response_codes=[401, 403])
    @authentication.authenticate_access_token
    def post(self, request, *args, **kwargs):
        session = request.user
        session.delete()
        return Response(data=detail_message("Success"), status=status.HTTP_200_OK)
