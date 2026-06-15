from drf_spectacular.utils import OpenApiExample
from rest_framework import generics, status
from rest_framework.response import Response

from construction_work.models.manage_models import Device
from construction_work.serializers.device_serializers import (
    DeleteDeviceDataResponseSerializer,
)
from core.exceptions import MissingDeviceIdHeader
from core.utils.openapi_utils import (
    extend_schema_for_device_id,
)
from core.views.mixins import DeviceIdMixin


class DeleteDeviceDataView(DeviceIdMixin, generics.DestroyAPIView):
    """
    API view to remove all construction-work data linked to a device.
    """

    @extend_schema_for_device_id(
        success_response=DeleteDeviceDataResponseSerializer,
        exceptions=[MissingDeviceIdHeader],
        examples=[
            OpenApiExample(
                "Device data deleted",
                value={
                    "status": "deleted",
                    "message": "Device linked construction-work data removed.",
                },
            ),
            OpenApiExample(
                "Device already absent",
                value={
                    "status": "already_absent",
                    "message": "No device linked construction-work data found.",
                },
            ),
        ],
    )
    def delete(self, request, *args, **kwargs):
        deleted_count, _ = Device.objects.filter(device_id=self.device_id).delete()

        if deleted_count:
            return Response(
                data={
                    "status": "deleted",
                    "message": "Device linked construction-work data removed.",
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            data={
                "status": "already_absent",
                "message": "No device linked construction-work data found.",
            },
            status=status.HTTP_200_OK,
        )
