from typing import Tuple

from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from city_pass import authentication, models, serializers


class SessionInitView(generics.RetrieveAPIView):
    serializer_class = serializers.SessionInitOutSerializer
    authentication_classes = [authentication.APIKeyAuthentication]

    def get(self, request, *args, **kwargs):
        access_token, refresh_token = self.init_session()
        serializer = self.get_serializer(
            {"access_token": access_token, "refresh_token": refresh_token}
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
