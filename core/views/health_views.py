import logging

from django.db import connections
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class HealthCheckView(GenericAPIView):
    authentication_classes = []

    def get(self, request, *args, **kwargs) -> Response:
        """Health Check"""
        try:
            connections["default"].cursor()
        except BaseException:
            return Response(
                {"status": "unready"}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return Response({"status": "ok"})
