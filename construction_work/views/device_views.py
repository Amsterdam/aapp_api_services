from rest_framework import generics, status
from rest_framework.response import Response

from construction_work.models.manage_models import Device
from core.utils.openapi_utils import (
    extend_schema_for_device_id,
)
from core.views.mixins import DeviceIdMixin


class DeleteDeviceDataView(DeviceIdMixin, generics.GenericAPIView):
    """
    API view to remove all construction-work data linked to a device.
    """

    @extend_schema_for_device_id(
        success_response=None,
        success_status_code=204,
    )
    def delete(self, request, *args, **kwargs):
        Device.objects.filter(device_id=self.device_id).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
