from typing import Tuple

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from city_pass import authentication, models, serializers


class SessionInitView(generics.RetrieveAPIView):
    authentication_classes = [authentication.APIKeyAuthentication]
    serializer_class = serializers.SessionInitOutSerializer

    def get(self, request, *args, **kwargs):
        access_token_str, refresh_token_str = self.init_session()
        serializer = self.get_serializer(
            {"access_token": access_token_str, "refresh_token": refresh_token_str}
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def init_session(self) -> Tuple[str, str]:
        new_session = models.Session()
        access_token = models.AccessToken(session=new_session)
        refresh_token = models.RefreshToken(session=new_session)

        new_session.save()
        access_token.save()
        refresh_token.save()
        return access_token.token, refresh_token.token


class SessionPostCredentialView(generics.CreateAPIView):
    authentication_classes = [authentication.APIKeyAuthentication]
    serializer_class = serializers.SessionCityPassCredentialSerializer

    @extend_schema(
        responses={
            200: serializers.SessionResultSerializer,
            401: serializers.SessionResultSerializer,
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        access_token = models.AccessToken.objects.filter(
            token=validated_data["session_token"]
        ).first()
        if not access_token:
            return Response(
                data={"result": "Session token is invalid"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not access_token.is_valid():
            return Response(
                data={"result": "Session token is expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token.session.encrypted_adminstration_no = validated_data[
            "encrypted_administration_no"
        ]
        access_token.session.save()

        return Response(data={"result": "Success"}, status=status.HTTP_200_OK)


# TODO
class SessionRefreshAccessView(generics.CreateAPIView):
    pass
